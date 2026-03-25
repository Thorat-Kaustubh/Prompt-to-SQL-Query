import os
import asyncio
import time
import json
import re
from typing import Optional, Dict, Any, List, Type, Callable
from loguru import logger
import litellm

# --- EXECUTION CONTROLLER ---
CONCURRENCY_LIMITS = {"gemini": 2, "groq": 5}
MODEL_FALLBACK_CHAIN = [
    os.getenv("GEMINI_LITE", "gemini/gemini-2.5-flash-lite"),
    os.getenv("GEMINI_FLASH", "gemini/gemini-2.5-flash")
]

class ExecutionController:
    def __init__(self):
        self._semaphores_instance = None
        self._circuit_breakers = {"gemini": 0, "groq": 0}
        self._failure_counts = {"gemini": 0, "groq": 0}
        litellm.telemetry = False 

    @property
    def _semaphores(self):
        if self._semaphores_instance is None:
            self._semaphores_instance = {
                "gemini": asyncio.Semaphore(CONCURRENCY_LIMITS["gemini"]),
                "groq": asyncio.Semaphore(CONCURRENCY_LIMITS["groq"])
            }
        return self._semaphores_instance
        
    async def _call_llm(self, prompt: str, model: str, priority: str = "medium", metadata: Dict[str, Any] = None) -> str:
        provider = "gemini" if "gemini" in model.lower() else "groq"
        if time.time() < self._circuit_breakers[provider]:
            raise Exception(f"Circuit Breaker active for {provider}")
        if priority == "low": await asyncio.sleep(0.5)

        async with self._semaphores.get(provider, self._semaphores["gemini"]):
            for attempt in range(4):
                start_time = time.time()
                try:
                    response = await _original_acompletion(model=model, messages=[{"role": "user", "content": prompt}], temperature=0.1)
                    self._failure_counts[provider] = 0
                    return response.choices[0].message.content
                except Exception as e:
                    err_str = str(e).lower()
                    if ("429" in err_str or "rate" in err_str) and attempt < 3:
                        await asyncio.sleep(2 * (attempt + 1))
                        continue
                    self._failure_counts[provider] += 1
                    if self._failure_counts[provider] >= 3: self._circuit_breakers[provider] = time.time() + 60
                    raise e

    async def execute_task(self, prompt: str, preferred_model: Optional[str] = None, priority: str = "medium") -> Dict[str, Any]:
        start_idx = 0
        if preferred_model:
            try: start_idx = MODEL_FALLBACK_CHAIN.index(preferred_model)
            except ValueError: pass
        for i in range(start_idx, len(MODEL_FALLBACK_CHAIN)):
            current_model = MODEL_FALLBACK_CHAIN[i]
            try:
                result = await self._call_llm(prompt, current_model, priority)
                return {"content": result, "model": current_model, "error": None}
            except Exception as e:
                logger.error(f"Execution Controller: ⚠️ {current_model} failed: {str(e)}")
        return {"content": "", "error": "No models available."}

_controller: Optional[ExecutionController] = None
def get_controller() -> ExecutionController:
    global _controller
    if _controller is None: _controller = ExecutionController()
    return _controller

_original_acompletion = litellm.acompletion
_original_completion = litellm.completion

async def intercepted_acompletion(*args, **kwargs):
    model = kwargs.get("model", "")
    messages = kwargs.get("messages", [])
    prompt = messages[-1]["content"] if messages else ""
    res = await get_controller().execute_task(prompt, preferred_model=model)
    if res.get("error"): return await _original_acompletion(*args, **kwargs)
    class InterceptedResponse:
        def __init__(self, content, model_name):
            self.choices = [type('Choice', (), {'message': type('Message', (), {'content': content, 'role': 'assistant', 'tool_calls': None})})]
            self.model = model_name
            self.usage = type('Usage', (), {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0})
    return InterceptedResponse(res["content"], res["model"])

litellm.acompletion = intercepted_acompletion

# --- AUDITED & IMPROVED COMPONENTS ---

class Guardrail:
    """
    SECURITY LAYER: Prompt Injection & Query Sanitization.
    """
    @staticmethod
    def sanitize(query: str) -> str:
        # Detect attempt to break out of delimiters or bypass instructions
        forbidden = ["ignore previous instructions", "system prompt", "delete all", "drop database"]
        clean_query = query.strip()
        for pattern in forbidden:
            if pattern in clean_query.lower():
                logger.warning(f"Guardrail: Potential injection attempt blocked: {pattern}")
                raise ValueError(f"Security Policy Violation: Query contains forbidden logic.")
        return clean_query

class FewShotLibrary:
    """
    SYNCHRONIZED EXAMPLES: Aligned with executor/engine.py schema.
    Schema: Users (id, name, email, role, created_at), Products (name, price, stock, category_id), Categories (name)
    """
    EXAMPLES = {
        "Aggregation": [
            {"q": "How many users joined since 2024?", "sql": "SELECT COUNT(*) FROM users WHERE created_at >= '2024-01-01';"},
            {"q": "Top products by stock", "sql": "SELECT name, stock FROM products ORDER BY stock DESC LIMIT 5;"}
        ],
        "Join": [
            {"q": "List products with their category names", "sql": "SELECT p.name, c.name as category FROM products p JOIN categories c ON p.category_id = c.id;"},
            {"q": "Total stock per category", "sql": "SELECT c.name, SUM(p.stock) FROM categories c JOIN products p ON c.id = p.category_id GROUP BY 1;"}
        ],
        "Filter": [
            {"q": "Admins with email containing 'google'", "sql": "SELECT name, email FROM users WHERE role = 'admin' AND email LIKE '%google%';"},
            {"q": "Categories with no products", "sql": "SELECT c.name FROM categories c LEFT JOIN products p ON c.id = p.category_id WHERE p.id IS NULL;"}
        ],
        "Complex": [
            {"q": "Highly active categories (average stock > 100)", "sql": "SELECT c.name FROM categories c JOIN products p ON c.id = p.category_id GROUP BY 1 HAVING AVG(p.stock) > 100;"}
        ]
    }

    @classmethod
    def get_examples(cls, category: str) -> str:
        examples = cls.EXAMPLES.get(category, cls.EXAMPLES["Aggregation"])
        return "\n".join([f"Prompt: \"{ex['q']}\"\nResponse SQL: {ex['sql']}\n" for ex in examples[:2]])

class QueryClassifier:
    def __init__(self, controller: ExecutionController):
        self.controller = controller

    async def classify(self, query: str) -> str:
        prompt = f"Classify query type for Text-to-SQL intent: [Aggregation, Join, Filter, Sorting, Complex]. Query: \"{query}\". Return ONE word only."
        res = await self.controller.execute_task(prompt, preferred_model=os.getenv("GEMINI_LITE"))
        category = res["content"].strip().title()
        return category if category in ["Aggregation", "Join", "Filter", "Sorting", "Complex"] else "Complex"

class PromptBuilder:
    def __init__(self, dialect: str = "PostgreSQL"):
        self.dialect = dialect
        self.rules = [
            f"Output valid {self.dialect} only.",
            "LIMIT results to 50 unless specified.",
            "Never use SELECT *. List columns explicitly.",
            "Use clear table aliases.",
            "READ-ONLY: Block all DDL/DML (DELETE, DROP, TRUNCATE, UPDATE)."
        ]

    def build(self, query: str, schema: str, history: str, category: str, error_context: Optional[Dict[str, Any]] = None, semantic_context: Optional[str] = None, attempt_info: Optional[Dict[str, int]] = None) -> str:
        # Context Management: Limit history to last 2000 chars
        truncated_history = history[-2000:] if history else "No history."
        
        # 1. Semantic Intelligence Injection
        semantic_block = ""
        if semantic_context:
            semantic_block = f"\n{semantic_context}\n"
        
        examples = FewShotLibrary.get_examples(category)
        
        # 5. UNIFIED SELF-HEALING BLOCK (Audit Improved)
        error_block = ""
        if error_context:
            # Error Categorization Refinement
            err_msg = error_context.get("error", "").lower()
            if "unauthorized" in err_msg or "permission" in err_msg:
                err_type = "SECURITY_VIOLATION"
            elif "column" in err_msg:
                err_type = "MISSING_COLUMN"
            elif "table" in err_msg or "relation" in err_msg:
                err_type = "INVALID_TABLE_REFERENCE"
            elif "syntax" in err_msg:
                err_type = "SYNTAX_ERROR"
            else:
                err_type = "GENERIC_DATABASE_ERROR"

            failed_sql = error_context.get("sql", "Unknown SQL")
            attempt_str = ""
            if attempt_info:
                attempt_str = f" (Attempt {attempt_info['current']} of {attempt_info['max']})"

            error_block = f"""
### ⚠️ SELF-HEALING CONTEXT{attempt_str}
Detected Error Type: {err_type}
- **FAILED SQL:** `{failed_sql}`
- **ERROR MESSAGE:** `{error_context.get('error')}`

**RECOVERY INSTRUCTIONS:**
1. Focus specifically on fixing the `{err_type}`.
2. If it is a MISSING_COLUMN, verify if you should be using a different column from the schema or if a JOIN is required to reach the correct table.
3. If it is an INVALID_TABLE_REFERENCE, ensure you are using exactly the table names provided in the 'Database Schema'.
4. Ensure the corrected SQL is syntactically valid and efficient.
"""

        return f"""
        ### Task: Convert to {self.dialect} SQL.
        ### Format: JSON object with keys: "sql", "explanation", "complexity", "visualization".

        ### Database Schema:
        {schema}

        {semantic_block}
        ### Recent History:
        {truncated_history}

        ### Few-Shot Examples ({category}):
        {examples}

        ### Precision Guardrails:
        {" ".join([f"{i+1}. {r}" for i, r in enumerate(self.rules)])}
        {error_block}

        ### User Input:
        {query}

        ### Final Output (JSON):
        """

class LLMEngine:
    def __init__(self, dialect: str = "PostgreSQL"):
        self.controller = get_controller()
        self.classifier = QueryClassifier(self.controller)
        self.builder = PromptBuilder(dialect=dialect)

    async def generate_sql(self, user_query: str, schema_context: str, history_context: str, error_context: Optional[Dict[str, Any]] = None, semantic_context: Optional[str] = None, attempt_info: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        AI SQL GENERATOR (Stateless).
        Produces a single generation attempt based on the provides context and optional error feedback.
        """
        # 1. Sanitization
        try:
            clean_query = Guardrail.sanitize(user_query)
        except ValueError as e:
            return {"sql": "", "error": str(e), "status": "Blocked"}
        # 2. Classification
        category = await self.classifier.classify(clean_query)

        # 3. Generation
        prompt = self.builder.build(
            clean_query, 
            schema_context, 
            history_context, 
            category, 
            error_context=error_context,
            semantic_context=semantic_context,
            attempt_info=attempt_info
        )
        
        logger.info(f"LLM Engine: Generating SQL for query type '{category}'...")
        res = await self.controller.execute_task(prompt, preferred_model=os.getenv("GEMINI_FLASH"))
        
        if res.get("error"):
            logger.error(f"LLM Engine: Generation failed: {res['error']}")
            return {"sql": "", "error": res["error"], "status": "Failed"}

        # 4. Parsing & Cleansing
        parsed_result = self._cleanse_sql(res["content"])
        
        return {
            **parsed_result,
            "category": category,
            "status": "Generated",
            "model": res.get("model")
        }

    def _cleanse_sql(self, raw_response: str) -> Dict[str, Any]:
        """
        Extracts JSON block from LLM output.
        """
        try:
             match = re.search(r'\{.*\}', raw_response, re.DOTALL)
             if match: return json.loads(match.group(0))
        except: pass
        
        # Fallback to direct SQL extraction if JSON parsing fails
        sql_match = re.search(r'```sql\s*(.*?)\s*```', raw_response, re.DOTALL | re.IGNORECASE)
        extracted_sql = sql_match.group(1).strip() if sql_match else raw_response.strip()
        return {"sql": extracted_sql, "explanation": "Partial parse.", "complexity": "Medium", "visualization": "Table"}
