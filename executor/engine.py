import os
import time
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from loguru import logger

class QueryExecutor:
    """
    EXECUTOR MODULE (executor/) - Security Architect Refactored
    - Executes deterministic actions on SUPABASE POSTGRESQL.
    - NO Service Role Key used for user queries.
    - REQUIRES User JWT to enforce Row Level Security (RLS).
    - Uses 'execute_sql' RPC to run AI-generated SQL while maintaining SECURITY INVOKER.
    """
    def __init__(self, jwt_token: Optional[str] = None):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        # In a production backend, we initialize a user-specific client for RLS
        # Or we set the headers dynamically.
        self.supabase: Client = create_client(self.url, self.key)
        if jwt_token:
             # This ensures all Postgrest / RPC calls are made as the USER, enforcing RLS.
             self.supabase.postgrest.auth(jwt_token)
             logger.info("Executor Module: User identity attached to database session.")
        else:
             logger.warning("Executor Module: Running without user context. Queries may be EMPTY due to RLS.")

    def execute(self, sql: str) -> Dict[str, Any]:
        """
        Executes raw SQL using the execute_sql RPC (SECURITY INVOKER).
        - RLS is automatically enforced by the database server based on the JWT.
        """
        start_time = time.time()
        logger.info(f"Executor Module: Executing SQL via Supabase RPC: {sql}")
        
        try:
             # Calling our secure RPC function defined in utils/supabase_setup.sql
             # The database will use the user's JWT context from the request headers
             # to decide if the query is authorized under RLS policies.
             # Note: For multiple rows/complex results, the RPC would return json[].
             response = self.supabase.rpc("execute_sql", {"sql_query": sql}).execute()
             
             data = response.data if response.data else []
             # If result is a single dict (common for some RPC wrappers), wrap in list
             if isinstance(data, dict):
                  data = [data]
             
             execution_ms = (time.time() - start_time) * 1000
             logger.info(f"Executor Module: Result {len(data)} rows ({execution_ms:.2f}ms).")
             
             return {
                 "data": data,
                 "execution_ms": execution_ms,
                 "error": None
             }
                  
        except Exception as e:
             logger.error(f"Executor Module: BLOCKED or FAILED: {str(e)}")
             # Standardizing error for the LLM "Self-Correction" phase (Phase 11)
             raise Exception(f"Database Security Violation or Syntax Error: {str(e)}")

    def get_schema_context_raw(self) -> str:
        """
        Retrieves schema info. In production, this can be cached from Information Schema.
        """
        return """
        Table: Users (id, name, email, role, created_at)
        Table: Products (name, price, stock, category_id)
        Table: Categories (name)
        (RLS ENFORCED: Policies based on auth.uid())
        """

if __name__ == "__main__":
    pass
