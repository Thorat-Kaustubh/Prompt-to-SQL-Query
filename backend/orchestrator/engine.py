import os
import asyncio
import time
import uuid
from typing import Dict, Any, Optional, List
from loguru import logger

from auth.engine import AuthEngine
from memory.engine import MemoryEngine
from llm.engine import LLMEngine
from validator.engine import SQLValidator
from executor.engine import QueryExecutor 
from cache.engine import RedisCache
from visualization.engine import VisualizationEngine
from semantic.engine import SemanticTranslator
from utils.logger import StructuredLogger, set_request_id

class QueryOrchestrator:
    """
    SENIOR AI SYSTEMS ARCHITECT - CENTRAL ORCHESTRATOR
    - Role: Deterministic Flow Controller for the AI Pipeline.
    - Responsibilities: Sequencing, Parallelization, Retry Logic, Error Categorization.
    - Constraints: Stateless, No business logic, No direct DB access.
    """
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
        
        logger.info("Orchestrator: Central Control Layer Initialized.")

    async def execute_pipeline(self, user_query: str, jwt_token: str) -> Dict[str, Any]:
        """
        Main Execution Lifecycle: 
        Auth -> Context (Parallel) -> Generate -> Validate -> Execute -> Loop (Retry) -> Cache -> Respond.
        """
        request_id = str(uuid.uuid4())
        set_request_id(request_id)
        start_time = time.time()
        
        # 1. LOG ENTRY (Observability MVP)
        StructuredLogger.log_event("REQUEST_RECEIVED", {
            "query": user_query,
            "jwt_token": jwt_token, # Will be redacted by internal logger logic
        })

        try:
            # 1. AUTHENTICATION & IDENTITY
            identity = self.auth.verify_auth_identity(jwt_token)
            if not identity:
                err_msg = "Authentication Failed: Invalid token."
                StructuredLogger.log_event("REQUEST_FAILED", {
                    "query": user_query,
                    "status": "FAILED",
                    "error": err_msg,
                    "execution_time_ms": (time.time() - start_time) * 1000
                })
                return {"error": err_msg, "status": "Unauthorized"}
            
            user_id = identity['user_id']
            user_role = identity.get('role', 'user')
            schema_version = "v1" # Tracked for cache consistency
            logger.info(f"Step 1 [AUTH SUCCESS]: User '{user_id}' ({user_role}) verified.")

            # RBAC: Define table whitelist based on role
            role_whitelist = {"products", "categories"}
            if user_role == "admin": role_whitelist.add("users")
            
            # --- LEVEL 1 CACHE: QUERY -> SQL ---
            cached_sql = self.cache.get_sql_cache(user_query, user_id, schema_version)
            sql = None
            l1_hit = False

            if cached_sql:
                logger.info("Step 2 [L1 CACHE HIT]: SQL found in Redis.")
                sql = cached_sql
                l1_hit = True
            else:
                logger.info("Step 2 [L1 CACHE MISS]: Continuing to AI generation.")

            # 3. SEMANTIC RESOLUTION
            logger.info("Step 3 [SEMANTIC]: Resolving business intent...")
            semantic_res = self.semantic.translate(user_query)
            semantic_context = semantic_res.get("semantic_context", "")

            # 4. CONTEXT RETRIEVAL
            memory_engine = self.memory if self.memory else MemoryEngine(user_id=user_id)
            executor_instance = self.executor_class(jwt_token=jwt_token)
            
            # Fetch Schema (Parallel with history)
            schema_task = asyncio.to_thread(executor_instance.get_schema_context_raw, role_whitelist)
            history_task = asyncio.to_thread(memory_engine.get_context, user_query)
            schema, history = await asyncio.gather(schema_task, history_task)

            # 5. UNIFIED SELF-HEALING LOOP (Generation -> Validation -> Execution)
            max_retries, attempts, last_error = 3, 0, None
            execution_res = None
            gen_result = {"status": "Generated", "iterations": 0}
            l2_hit = False
            final_sql = sql # Use cached_sql if available

            while attempts < max_retries:
                attempts += 1
                logger.info(f"--- ATTEMPT {attempts} / {max_retries} ---")

                # A. GENERATION (Only if we don't have a query yet or the previous one failed)
                if not final_sql:
                    logger.info(f"Step 5.A [LLM GENERATION]: Attempting correction...")
                    gen_start = time.time()
                    gen_result = await self.llm.generate_sql(
                        user_query, 
                        schema, 
                        history, 
                        error_context=last_error,
                        semantic_context=semantic_context,
                        attempt_info={"current": attempts, "max": max_retries}
                    )
                    gen_ms = (time.time() - gen_start) * 1000
                    
                    if gen_result.get("error"): 
                        StructuredLogger.log_event("GENERATION_FAILED", {
                            "user_id": user_id,
                            "query": user_query,
                            "error": gen_result["error"],
                            "attempt": attempts,
                            "latency_ms": gen_ms
                        })
                        return {"error": gen_result["error"], "status": "Failed", "attempts": attempts}
                    
                    final_sql = gen_result.get("sql")
                    StructuredLogger.log_event("SQL_GENERATED", {
                        "user_id": user_id,
                        "query": user_query,
                        "sql": final_sql,
                        "attempt": attempts,
                        "latency_ms": gen_ms
                    })

                # B. VALIDATION
                logger.info(f"Step 5.B [VALIDATION]: Checking SQL safety...")
                validation = self.validator.validate_query(final_sql, table_whitelist=role_whitelist)
                if not validation["is_valid"]:
                    err_msg = validation["error"]
                    if validation.get("is_fatal", True): 
                        StructuredLogger.log_event("VALIDATION_FAILED", {"sql": final_sql, "error": err_msg, "is_fatal": True})
                        return {"error": f"Security: {err_msg}", "status": "Forbidden", "attempts": attempts}
                    
                    logger.warning(f"Validation Failed (Retryable): {err_msg}")
                    StructuredLogger.log_event("VALIDATION_FAILED", {"sql": final_sql, "error": err_msg, "is_fatal": False})
                    
                    # Store context for healing
                    last_error = {"type": "Validation", "sql": final_sql, "error": err_msg}
                    final_sql = None # Force regeneration
                    continue

                final_sql = validation["query"]

                # C. L2 CACHE CHECK (Only on first attempt of a specific SQL)
                if attempts == 1 or (not l1_hit and attempts == 1):
                    cached_res = self.cache.get_result_cache(final_sql, user_id, schema_version)
                    if cached_res:
                        logger.info("Step 5.C [L2 CACHE HIT]: Result found in Redis.")
                        execution_res = cached_res
                        l2_hit = True
                        break

                # D. DATABASE EXECUTION
                logger.info(f"Step 5.D [DB EXECUTION]: Running SQL...")
                execution_res = executor_instance.execute(final_sql)
                
                if execution_res.get("error"):
                    err_msg = execution_res["error"]
                    logger.warning(f"Execution Failed: {err_msg}")
                    StructuredLogger.log_event("EXECUTION_FAILED", {
                        "sql": final_sql, 
                        "error": err_msg, 
                        "latency_ms": execution_res.get("execution_ms", 0)
                    })
                    
                    # Cache Poisoning Prevention
                    if l1_hit and attempts == 1:
                        self.cache.delete_sql_cache(user_query, user_id, schema_version)
                    
                    last_error = {"type": "Execution", "sql": final_sql, "error": err_msg}
                    final_sql = None # Force regeneration
                    l1_hit = False
                    continue

                # SUCCESS: Break the loop
                logger.info(f"Step 5.E [SUCCESS]: Query resolved on attempt {attempts}.")
                break

            # Check if we exhausted retries
            if not execution_res or execution_res.get("error"):
                logger.error(f"SELF-HEALING FAILED: Exhausted {max_retries} attempts.")
                err_report = "Unable to generate valid SQL after multiple attempts."
                StructuredLogger.log_event("PIPELINE_FINAL_FAILURE", {
                    "user_id": user_id,
                    "query": user_query,
                    "error": err_report,
                    "attempts": attempts
                })
                return {
                    "status": "FAILED",
                    "reason": err_report,
                    "attempts": attempts,
                    "last_error": last_error
                }

            # 6. VISUALIZATION & RESPONSE CONSTRUCTION
            logger.info("Step 6 [VISUALIZATION]: Generating output metadata...")
            viz_output = self.visualization.analyze_and_configure(
                execution_res["data"],
                execution_ms=execution_res.get("execution_ms", 0.0)
            )

            total_time_ms = (time.time() - start_time) * 1000
            final_response = {
                "summary": viz_output["summary"],
                "results": viz_output["table"],
                "sql": final_sql,
                "visualization": viz_output["chart"],
                "meta": {
                    "execution_ms": total_time_ms,
                    "iterations": attempts,
                    "cached": l1_hit or l2_hit,
                    "detected_type": viz_output["metadata"]["detected_type"]
                }
            }

            # Final Observation Log (Success)
            StructuredLogger.log_event("PIPELINE_COMPLETE", {
                "user_id": user_id,
                "query": user_query,
                "sql": final_sql,
                "execution_time_ms": total_time_ms,
                "cache_hit": l1_hit or l2_hit,
                "status": "SUCCESS",
                "rows_returned": len(execution_res["data"]),
                "attempts": attempts
            })

            # 8. ASYNC POST-PROCESS
            async def background_post_process(q, s, r, uid, sv, do_l1, do_l2):
                 try:
                     memory_engine.add_interaction(q, f"SQL: {s}")
                     if do_l1: self.cache.set_sql_cache(q, s, uid, sv)
                     if do_l2: self.cache.set_result_cache(s, r, uid, sv)
                 except Exception as e: logger.warning(f"Persistence Failed: {str(e)}")

            asyncio.create_task(background_post_process(
                user_query, final_sql, final_response, user_id, schema_version, 
                not l1_hit, not l2_hit
            ))
            
            return final_response

        except Exception as e:
            total_time_ms = (time.time() - start_time) * 1000
            StructuredLogger.log_event("CRITICAL_FAILURE", {
                "query": user_query,
                "error": str(e),
                "execution_time_ms": total_time_ms,
                "status": "FAILED"
            })
            return {"error": f"Orchestrator Fatal Panic: {str(e)}", "status": "Panic"}
