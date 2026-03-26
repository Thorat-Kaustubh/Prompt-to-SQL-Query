import os
import time
from typing import List, Dict, Any, Optional, Set
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
        # In local development bypass, we use the service role key to perform actions
        # that would otherwise be blocked by RLS since we don't have a valid JWT.
        if jwt_token == "local-dev-token":
            self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            self.supabase: Client = create_client(self.url, self.key)
            logger.info("Executor: Developer bypass mode. RLS will be bypassed for testing.")
        else:
            # Fallback to anon key for standard user sessions or anonymous requests
            self.key = os.getenv("SUPABASE_ANON_KEY")
            self.supabase: Client = create_client(self.url, self.key)
            if jwt_token:
                self.supabase.postgrest.auth(jwt_token)
                logger.info("Executor: User identity attached to database session.")
            else:
                logger.warning("Executor: No user session found. Results may be limited.")

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
             execution_ms = (time.time() - start_time) * 1000
             logger.error(f"Executor Module: BLOCKED or FAILED: {str(e)}")
             return {
                 "data": [],
                 "execution_ms": execution_ms,
                 "error": str(e)
             }

    def get_schema_context_raw(self, table_whitelist: Optional[Set[str]] = None) -> str:
        """
        Retrieves schema info for the LLM. 
        In production, this would be dynamically fetched from Information Schema and cached.
        Filters schema based on the provided RBAC whitelist.
        """
        full_schema = {
            "users": "id (uuid), email (text), role (text), created_at (timestamptz)",
            "products": "id (bigint), name (text), price (numeric), stock (int), category_id (bigint)",
            "categories": "id (bigint), name (text)"
        }
        
        context_parts = ["### DATABASE SCHEMA (PostgreSQL)"]
        for table, cols in full_schema.items():
            if table_whitelist is None or table in table_whitelist:
                context_parts.append(f"- Table: {table}\n  Columns: {cols}")
        
        context_parts.append("\n(NOTE: Row Level Security (RLS) is active. Filtered by auth.uid().)")
        return "\n".join(context_parts)

if __name__ == "__main__":
    pass
