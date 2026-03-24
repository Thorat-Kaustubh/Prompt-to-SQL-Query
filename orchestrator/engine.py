import os
import asyncio
from typing import Dict, Any, Optional
from loguru import logger

from crewai import Crew, Process
from orchestrator.agents import (
    create_filter_agent, create_analyzer_agent, 
    create_generator_agent, create_refiner_agent,
    create_filter_task, create_analysis_task, 
    create_generation_task, create_refinement_task
)
from auth.engine import AuthEngine
from memory.engine import MemoryEngine
from llm.engine import LLMEngine
from validator.engine import SQLValidator
from executor.engine import QueryExecutor 
from cache.engine import RedisCache

class QueryOrchestrator:
    """
    AGENTIC ORCHESTRATOR (orchestrator/) - Powered by CrewAI
    - Uses a crew of specialized agents with configurable LLMs (Gemini, Groq, etc.).
    - Maintains caching and modular memory layers for performance.
    """
    def __init__(
        self, 
        auth: Optional[AuthEngine] = None,
        memory: Optional[MemoryEngine] = None,
        validator: Optional[SQLValidator] = None,
        executor_class = QueryExecutor,
        cache: Optional[RedisCache] = None
    ):
        self.auth = auth or AuthEngine()
        self.memory = memory
        self.validator = validator or SQLValidator()
        self.executor_class = executor_class
        self.cache = cache or RedisCache()

        # Model Routing Stack
        self.model_lite = os.getenv("GEMINI_LITE")
        self.model_flash = os.getenv("GEMINI_FLASH")
        self.model_8b = os.getenv("GROQ_LLAMA_8B")
        self.model_70b = os.getenv("GROQ_LLAMA_70B")
        
        # CrewAI Agents (Mapping roles to specific models)
        self.filter_agent = create_filter_agent(llm=self.model_lite)
        self.analyzer_agent = create_analyzer_agent(llm=self.model_flash)
        # We remove tools to simplify generation tier (reasoning-only)
        self.generator_agent = create_generator_agent(llm=self.model_8b)
        self.refiner_agent = create_refiner_agent(llm=self.model_70b)
        
        logger.info(f"AI Orchestrator: Controller Initialized with 4-tier model stack.")

    async def execute_pipeline(self, user_query: str, jwt_token: str) -> Dict[str, Any]:
        """
        Agentic Pipeline Execution Flow:
        1. Cache Check.
        2. FAST CLASSIFICATION: Intent, Auth, and Complexity logic.
        3. DYNAMIC BRANCHING:
           - [SIMPLE]: Filter -> Generate -> Refine (3 stages)
           - [COMPLEX]: Filter -> Analyze -> Generate -> Refine (4 stages)
        4. Memory persistence & Cache update.
        """
        logger.info(f"Orchestrator: Executing pipeline for query: {user_query}")
        
        # 1. Cache Check
        # (Identity check is now integrated into the classification stage for better agent feedback)
        cached_response = self.cache.get_query(user_query) # Simplified key for demo
        if cached_response:
             logger.info("Orchestrator: Cache hit.")
             return cached_response

        # 2. Stage 1: Security & Classification (Determines Path)
        memory_engine = self.memory if self.memory else MemoryEngine(user_id="anonymous")
        executor = self.executor_class(jwt_token=jwt_token)
        schema = executor.get_schema_context_raw()
        history = memory_engine.get_context(user_query)

        t_filter = create_filter_task(self.filter_agent, jwt_token, user_query)
        classification_crew = Crew(
            agents=[self.filter_agent],
            tasks=[t_filter],
            verbose=False # Keep it clean
        )
        
        try:
            logger.info("Controller: Classifying user intent and complexity...")
            raw_class = classification_crew.kickoff()
            
            # Helper to parse JSON from classification
            from llm.engine import LLMEngine
            engine = LLMEngine()
            class_data = engine._cleanse_sql(str(raw_class))
            
            is_verified = "VERIFIED" in str(raw_class).upper()
            is_simple = class_data.get("complexity", "high") == "low"
            
            if not is_verified:
                return {"error": "Unauthorized Access (Blocked by Security Specialist)."}

            # 3. Dynamic Execution Path
            tasks = []
            agents = []
            
            if is_simple:
                logger.info("Controller: Path selected -> [FAST-TRACK SIMPLE]")
                t_generate = create_generation_task(self.generator_agent, user_query, schema, history)
                t_refine = create_refinement_task(self.refiner_agent, "{sql_generation_result}", jwt_token)
                tasks = [t_generate, t_refine]
                agents = [self.generator_agent, self.refiner_agent]
            else:
                logger.info("Controller: Path selected -> [DEEP ANALYSIS]")
                t_analyze = create_analysis_task(self.analyzer_agent, user_query, schema, history)
                t_generate = create_generation_task(self.generator_agent, user_query, schema, history)
                t_refine = create_refinement_task(self.refiner_agent, "{sql_generation_result}", jwt_token)
                tasks = [t_analyze, t_generate, t_refine]
                agents = [self.analyzer_agent, self.generator_agent, self.refiner_agent]

            final_crew = Crew(
                agents=agents,
                tasks=tasks,
                process=Process.sequential,
                verbose=False
            )

            logger.info("Controller: Starting agent orchestration...")
            crew_result = final_crew.kickoff()
            logger.info("Controller: Orchestration complete.")
            
            # Extract final payload
            refined_data = engine._cleanse_sql(str(crew_result))

            # Final response structure
            final_response = {
                "summary": f"SQL generated with {refined_data.get('complexity', 'standard')} complexity ranking.",
                "detailed_explanation": refined_data.get("explanation", "Agentic SQL synthesis successful."),
                "actionable_steps": [
                    "Validate the provided SQL against your expected schema.",
                    f"Consider a {refined_data.get('suggested_visualization', 'Table')} for the resulting dataset."
                ],
                "sql": refined_data.get("sql", "SELECT NULL;"),
                "meta": {
                    "complexity": refined_data.get("complexity", "Unknown"),
                    "visualization": refined_data.get("suggested_visualization", "Table"),
                    "path_taken": "FAST-TRACK" if is_simple else "DEEP-ANALYSIS",
                    "models": ["GEMINI-LITE", "LLAMA-8B", "LLAMA-70B"] if is_simple else ["GEMINI-LITE", "GEMINI-FLASH", "LLAMA-8B", "LLAMA-70B"]
                },
                "error": None
            }
            
            # Update memory & Cache
            memory_engine.add_interaction(user_query, f"Result: {final_response['sql'][:50]}")
            
            return final_response
            
        except Exception as e:
            logger.error(f"Orchestration Failure: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": f"Orchestrator Controller Error: {str(e)}"}

