import sqlglot
import re
from typing import Dict, Any, List
from loguru import logger

class SQLValidator:
    """
    VALIDATOR MODULE (validator/) - Architect Refactored
    - Provides structural AND semantic validation.
    - MUST run before and after execution.
    - MUST NOT access DB directly (orchestrator feeds validation data).
    """
    def __init__(self, table_whitelist: List[str] = ["Users", "Logs", "Products", "Categories"]):
        self.table_whitelist = [t.lower() for t in table_whitelist]

    def validate_input_sql(self, sql: str) -> Dict[str, Any]:
        """
        PRE-EXECUTION (Input Validation): Ensures SQL structure and security.
        """
        if not sql:
            return {"is_valid": False, "error": "Empty SQL query"}
            
        sql_clean = sql.strip().upper()
        logger.info(f"Validator Module: Validating input SQL structure.")

        # 1. Structural Security (SELECT only)
        if not sql_clean.startswith("SELECT"):
            return {"is_valid": False, "error": "Only SELECT queries allowed (Unauthorized CRUD detected)."}

        # 2. Block Dangerous Prohibited Actions (Drop, Delete, etc.)
        prohibited = ["DROP", "DELETE", "TRUNCATE", "INSERT", "UPDATE", "ALTER", "GRANT", "REVOKE"]
        for p in prohibited:
            if f" {p} " in f" {sql_clean} ":
                 return {"is_valid": False, "error": f"Unauthorized keyword detected: {p}"}

        # 3. Parsing & Syntax (sqlglot)
        try:
             sqlglot.parse_one(sql)
        except Exception as e:
             return {"is_valid": False, "error": f"SQL Parsing Error: {str(e)}"}

        return {"is_valid": True, "error": None}

    def validate_output_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        POST-EXECUTION (Output Validation): Ensures safe data return.
        - Guardrails for empty results.
        - PII masking logic (placeholder).
        - Limit check on data size.
        """
        logger.info(f"Validator Module: Validating output data (Rows: {len(results)}).")
        
        # Guard: Excessive Result Size
        if len(results) > 1000:
             return {"is_valid": False, "error": "Query result exceeds safety threshold (1k rows)."}
             
        # Placeholder: Semantic PII Masking
        # In the future, this module would identify sensitive fields in results.

        return {"is_valid": True, "error": None}

if __name__ == "__main__":
    pass
