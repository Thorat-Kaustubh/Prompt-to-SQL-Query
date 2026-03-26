import os
import asyncio
import time
import uuid
import json
from typing import Dict, Any, Optional, List, AsyncGenerator
from loguru import logger

from auth.engine import AuthEngine
from memory.engine import MemoryEngine
from llm.engine import LLMEngine
from validator.engine import SQLValidator
from executor.engine import QueryExecutor 
from cache.engine import RedisCache
from visualization.engine import VisualizationEngine
from semantic.engine import SemanticTranslator
from orchestrator.agents import run_complex_query
from utils.logger import StructuredLogger, set_request_id

class QueryOrchestrator:
    def __init__(
        self, 
        auth: Optional[AuthEngine] = None,
        memory: Optional[MemoryEngine] = None,
        validator: Optional[SQLValidator] = None,
        executor_class = QueryExecutor,
        cache: Optional[RedisCache] = None,
        llm: Optional[LLMEngine] = None
    ):
        self.auth = auth or AuthEngine()
        self.memory = memory
        self.validator = validator or SQLValidator()
        self.executor_class = executor_class
        self.cache = cache or RedisCache()
        self.llm = llm or LLMEngine()
        self.visualization = VisualizationEngine()
        self.semantic = SemanticTranslator()
        logger.info("System Ready.")

    async def execute_pipeline(self, user_query: str, jwt_token: str) -> Dict[str, Any]:
        start_time = time.time()
        try:
            identity = self.auth.verify_auth_identity(jwt_token)
            if not identity: return {"error": "Unauthorized"}
            
            user_id = identity['user_id']
            user_role = identity.get('role', 'user')
            role_whitelist = {"products", "categories"}
            if user_role == "admin": role_whitelist.add("users")
            
            executor_instance = self.executor_class(jwt_token=jwt_token)
            schema = await asyncio.to_thread(executor_instance.get_schema_context_raw, role_whitelist)
            memory_engine = self.memory if self.memory else MemoryEngine(user_id=user_id)
            history = await asyncio.to_thread(memory_engine.get_context, user_query)

            gen_res = await self.llm.generate_response(user_query, schema, history)
            
            if gen_res.get("complexity") == "HIGH":
                agent_res = await asyncio.to_thread(run_complex_query, user_query, schema, history, jwt_token)
                return {**gen_res, **agent_res, "status": "Success"}

            if gen_res.get("intent") in ["GENERAL", "HYBRID"]:
                return {**gen_res, "status": "Success"}

            # Data Path
            final_sql = gen_res.get("sql")
            execution_res = executor_instance.execute(final_sql)
            
            if execution_res.get("error"):
                return {**gen_res, "error": execution_res["error"]}

            viz_output = self.visualization.analyze_and_configure(execution_res["data"])
            return {
                "status": "Success",
                **gen_res,
                "results": viz_output["table"],
                "visualization": viz_output["chart"]
            }

        except Exception as e:
            logger.error(f"Pipeline Failed: {e}")
            return {"error": str(e)}

    async def stream_pipeline(self, user_query: str, jwt_token: str) -> AsyncGenerator[str, None]:
        try:
            identity = self.auth.verify_auth_identity(jwt_token)
            if not identity:
                yield json.dumps({"error": "Unauthorized"})
                return

            user_id = identity['user_id']
            user_role = identity.get('role', 'user')
            role_whitelist = {"products", "categories"}
            if user_role == "admin": role_whitelist.add("users")

            executor_instance = self.executor_class(jwt_token=jwt_token)
            schema = await asyncio.to_thread(executor_instance.get_schema_context_raw, role_whitelist)
            memory_engine = self.memory if self.memory else MemoryEngine(user_id=user_id)
            history = await asyncio.to_thread(memory_engine.get_context, user_query)

            async for chunk in self.llm.generate_stream(user_query, schema, history):
                yield chunk
        except Exception as e:
            yield json.dumps({"error": str(e)})
