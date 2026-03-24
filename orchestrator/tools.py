from crewai.tools import BaseTool
from typing import Type, Optional, Dict, Any
from pydantic import BaseModel, Field
from auth.engine import AuthEngine
from llm.engine import LLMEngine
from validator.engine import SQLValidator
from executor.engine import QueryExecutor
from loguru import logger

# --- Tool Schemas ---

class IdentitySchema(BaseModel):
    jwt_token: str = Field(..., description="The user's Supabase JWT token for identity verification.")

class SQLGeneratorSchema(BaseModel):
    user_query: str = Field(..., description="The natural language query from the user.")
    schema_context: str = Field(..., description="The database schema information.")
    history_context: str = Field(..., description="The previous conversation context.")

class SQLValidatorSchema(BaseModel):
    sql: str = Field(..., description="The generated SQL to be validated for safety and structure.")

class DBExecutorSchema(BaseModel):
    sql: str = Field(..., description="The validated SQL query to execute against the database.")
    jwt_token: str = Field(..., description="The user's Supabase JWT token to enforce RLS.")

# --- CrewAI Tools ---

class VerifyIdentityTool(BaseTool):
    name: str = "verify_identity"
    description: str = "Verifies the user's identity and checks their role against the database using a Supabase JWT token."
    args_schema: Type[BaseModel] = IdentitySchema

    def _run(self, jwt_token: str) -> str:
        auth_engine = AuthEngine()
        identity = auth_engine.verify_auth_identity(jwt_token)
        if not identity:
            return "ERROR: Unauthorized access. Identity could not be verified."
        return f"SUCCESS: Identity verified. User ID: {identity['user_id']}, Role: {identity['role']}"

class SQLGeneratorTool(BaseTool):
    name: str = "generate_sql"
    description: str = "Converts a natural language query into a valid PostgreSQL query using the provided schema and history context."
    args_schema: Type[BaseModel] = SQLGeneratorSchema

    async def _arun(self, user_query: str, schema_context: str, history_context: str) -> str:
        llm_engine = LLMEngine()
        result = await llm_engine.generate_sql(user_query, schema_context, history_context)
        if result.get("error"):
            return f"ERROR: Failed to generate SQL: {result['error']}"
        return result["sql"]

    def _run(self, *args, **kwargs) -> str:
        # Fallback for sync execution (not recommended)
        import asyncio
        return asyncio.run(self._arun(*args, **kwargs))

class SQLValidatorTool(BaseTool):
    name: str = "validate_sql"
    description: str = "Validates the generated SQL for safety (SELECT only), proper LIMIT usage, and structural adherence."
    args_schema: Type[BaseModel] = SQLValidatorSchema

    def _run(self, sql: str) -> str:
        validator = SQLValidator()
        validation = validator.validate_input_sql(sql)
        if not validation["is_valid"]:
            return f"ERROR: SQL Validation failed: {validation['error']}"
        return "SUCCESS: SQL is valid and safe to execute."

class DBExecutorTool(BaseTool):
    name: str = "execute_db_query"
    description: str = "Executes a validated SQL query against the database while enforcing Row Level Security (RLS) via the user's JWT."
    args_schema: Type[BaseModel] = DBExecutorSchema

    def _run(self, sql: str, jwt_token: str) -> str:
        executor = QueryExecutor(jwt_token=jwt_token)
        try:
            result = executor.execute(sql)
            return f"SUCCESS: Query executed. Data: {result['data']}"
        except Exception as e:
            return f"ERROR: Database execution failed or security violation: {str(e)}"
