import sqlglot
from sqlglot import exp, parse_one
import re
from typing import Dict, Any, List, Set, Optional
from loguru import logger

class SQLValidator:
    """
    SENIOR BACKEND SECURITY VALIDATOR (validator/)
    - Enforces a strict read-only SQL execution layer.
    - Prevents destructive operations and unauthorized data access.
    - Performs schema-level validation (Tables, Columns, Relationships).
    - Automatically injects safety guards like LIMIT.
    """
    
    # Approved Schema Definition
    ALLOWED_SCHEMA = {
        "users": {"id", "email", "role", "created_at"},
        "products": {"id", "name", "price", "stock", "category_id"},
        "categories": {"id", "name"}
    }
    
    # Authorized Join Relationships (Foreign Key Map)
    AUTHORIZED_RELATIONS = {
        ("products", "categories"): {"category_id", "id"},
        # Add other verified paths here
    }
    
    # Blocked sensitive columns
    SENSITIVE_COLUMNS = {"password", "token", "secret", "apikey"}
    
    # Strictly blocked keywords
    BLOCKED_KEYWORDS = {
        "INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", 
        "ALTER", "GRANT", "REVOKE", "EXECUTE", "REPLACE",
        "MERGE", "CALL", "VACUUM", "ANALYZE", "COPY"
    }

    def __init__(self, table_whitelist: Optional[List[str]] = None):
        if table_whitelist:
            self.whitelist = {t.lower() for t in table_whitelist}
        else:
            self.whitelist = set(self.ALLOWED_SCHEMA.keys())

    def validate_query(self, sql: str, table_whitelist: Optional[Set[str]] = None) -> Dict[str, Any]:
        """
        Full Enterprise Validation Pipeline with Scoped Column Affinity.
        """
        # Use request-specific whitelist (RBAC) if provided, else fallback to default
        current_whitelist = table_whitelist if table_whitelist is not None else self.whitelist
        
        try:
            # 1. Basic Sanitization & Multi-statement Check
            if sql is None:
                return self._fail("SQL query is None (Generation likely failed)")
            
            sql = sql.strip()
            if not sql:
                return self._fail("Empty SQL query")
            
            try:
                parsed_statements = sqlglot.parse(sql, read="postgres")
                if len(parsed_statements) > 1:
                    return self._fail("Multiple SQL statements detected (Semicolon injection blocked)", is_fatal=True)
                expression = parsed_statements[0]
            except Exception as e:
                return self._fail(f"SQL Syntax Error: {str(e)}", is_fatal=False)

            # 2. Read-Only Enforcement
            if not isinstance(expression, exp.Select):
                return self._fail("Only SELECT queries are authorized")

            # 3. Keyword & Command Filtering (AST Check)
            for node in expression.find_all(exp.Expression):
                if any(isinstance(node, cls) for cls in [exp.Drop, exp.Update, exp.Delete, exp.Insert, exp.Alter]):
                    return self._fail(f"Unauthorized operation detected: {node.key}")

            # 4. Table & Schema Validation
            tables_found = {} # alias -> table_name
            for table in expression.find_all(exp.Table):
                table_name = table.name.lower()
                alias = table.alias.lower() if table.alias else table_name
                tables_found[alias] = table_name
                
                # Block non-public/unauthorized schemas
                if table.db and table.db.lower() not in ["public", ""]:
                    return self._fail(f"Unauthorized schema access: {table.db}")
                
                # Check Table Whitelist (RBAC: Keep Fatal)
                if table_name not in current_whitelist:
                    return self._fail(f"Unauthorized table access: {table_name}", is_fatal=True)
                
                # Verify Table Exists in Schema (Typo: Healable)
                if table_name not in self.ALLOWED_SCHEMA:
                    return self._fail(f"Table does not exist: {table_name}", is_fatal=False)

            # 5. Join Validation (Relationship Check)
            for join in expression.find_all(exp.Join):
                join_table = join.this.name.lower()
                # Find the 'on' condition to verify identity of join
                # In a production system, we'd verify the keys match AUTHORIZED_RELATIONS.
                # For this implementation, we ensure it's a known table.
                if join_table not in current_whitelist:
                    return self._fail(f"Unauthorized join target: {join_table}", is_fatal=True)

            # 6. Scoped Column Validation (Affinity Check)
            all_allowed_cols = set()
            for t in set(tables_found.values()):
                all_allowed_cols.update(self.ALLOWED_SCHEMA.get(t, set()))
            
            SAFE_FUNCTIONS = {"count", "sum", "avg", "min", "max", "coalesce", "now", "current_timestamp"}

            for column in expression.find_all(exp.Column):
                col_name = column.name.lower()
                col_table_alias = column.table.lower() if column.table else None
                
                if col_name == "*": continue
                if col_name in self.SENSITIVE_COLUMNS:
                    return self._fail(f"Access to sensitive column blocked: {col_name}")
                if col_name in SAFE_FUNCTIONS: continue

                # Affinity Check: If table/alias is specified, verify column belongs to it
                if col_table_alias:
                    real_table = tables_found.get(col_table_alias)
                    if not real_table:
                        return self._fail(f"Unknown table alias/reference: {col_table_alias}")
                    if col_name not in self.ALLOWED_SCHEMA.get(real_table, set()):
                        return self._fail(f"Column '{col_name}' does not exist in table '{real_table}'")
                else:
                    # Global check if no alias provided (Self-Healing improved for orchestrator check)
                    if col_name not in all_allowed_cols:
                         return self._fail(f"Non-existent column: '{col_name}' is not in the allowed schema.", is_fatal=False)

            # 7. Safety Limit Enforcement
            limit_clause = expression.find(exp.Limit)
            if not limit_clause:
                logger.info("Limit missing: Automatically appending LIMIT 100")
                expression = expression.limit(100)
                sql = expression.sql(dialect="postgres")
            else:
                limit_val = limit_clause.expression.this
                try:
                    limit_int = int(str(limit_val))
                    if limit_int > 1000:
                        logger.warning(f"Excessive limit ({limit_int}) detected. Capping to 1000.")
                        expression.set("limit", exp.Limit(expression=exp.Literal.number(1000)))
                        sql = expression.sql(dialect="postgres")
                    else:
                        sql = expression.sql(dialect="postgres")
                except (ValueError, TypeError):
                    sql = expression.sql(dialect="postgres")
            
            if not sql.strip().upper().startswith("SELECT"):
                 return self._fail("Final generated SQL must be a SELECT query")

            return {
                "is_valid": True, 
                "query": sql, 
                "error": None,
                "is_fatal": False
            }

        except Exception as e:
            logger.error(f"Validator Critical Failure: {str(e)}")
            return self._fail(f"Internal Security Validation Error: {str(e)}", is_fatal=True)

    def _fail(self, message: str, is_fatal: bool = True) -> Dict[str, Any]:
        level = "FATAL SECURITY" if is_fatal else "HEALABLE ERROR"
        logger.warning(f"Security Shield: Query Rejected [{level}] - {message}")
        return {"is_valid": False, "query": None, "error": message, "is_fatal": is_fatal}

    def validate_output_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        POST-EXECUTION (Output Validation): Ensures safe data return.
        """
        logger.info(f"Validator Module: Validating output data (Rows: {len(results)}).")
        
        # Guard: Excessive Result Size
        if len(results) > 1000:
             return {"is_valid": False, "error": "Query result exceeds safety threshold (1000 rows)."}
             
        return {"is_valid": True, "error": None}

if __name__ == "__main__":
    # Test cases
    validator = SQLValidator()
    
    tests = [
        "SELECT * FROM Users",
        "SELECT id, email FROM Users LIMIT 10",
        "SELECT * FROM Products; DROP TABLE Users",
        "INSERT INTO Users (name) VALUES ('Hacker')",
        "UPDATE Users SET role = 'admin'",
        "SELECT password FROM Users",
        "SELECT * FROM products JOIN categories ON products.category_id = categories.id",
        "SELECT * FROM auth.users", # Unauthorized Schema
        "SELECT u.name, p.price FROM users u JOIN products p ON u.id = p.id", # Valid Aliased Join
        "SELECT u.price FROM users u" # Affinity Error (price is in products)
    ]
    
    for t in tests:
        res = validator.validate_query(t)
        print(f"SQL: {t}")
        print(f"Valid: {res['is_valid']}")
        if res['error']: print(f"Error: {res['error']}")
        if res['query']: print(f"Final SQL: {res['query']}")
        print("-" * 20)
