import os
import asyncio
import time
import json
import re
from typing import Optional, Dict, Any, List, Type, Callable, AsyncGenerator
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
        
    async def _call_llm(self, messages: List[Dict[str, str]], model: str) -> str:
        provider = "gemini" if "gemini" in model.lower() else "groq"
        async with self._semaphores.get(provider, self._semaphores["gemini"]):
            for attempt in range(3):
                try:
                    res = await _original_acompletion(model=model, messages=messages, temperature=0.7)
                    return res.choices[0].message.content
                except Exception as e:
                    if attempt == 2: raise e
                    await asyncio.sleep(1)
        return ""

    async def _call_llm_stream(self, messages: List[Dict[str, str]], model: str) -> AsyncGenerator[str, None]:
        provider = "gemini" if "gemini" in model.lower() else "groq"
        async with self._semaphores.get(provider, self._semaphores["gemini"]):
            response = await _original_acompletion(model=model, messages=messages, temperature=0.7, stream=True)
            async for chunk in response:
                content = getattr(chunk.choices[0].delta, 'content', "") or ""
                yield content

    async def execute_task(self, messages: List[Dict[str, str]], preferred_model: Optional[str] = None) -> Dict[str, Any]:
        model = preferred_model or MODEL_FALLBACK_CHAIN[0]
        try:
            content = await self._call_llm(messages, model)
            return {"content": content, "model": model, "error": None}
        except Exception as e:
            logger.error(f"Task Failed: {e}")
            return {"content": "", "error": str(e), "model": model}

_controller: Optional[ExecutionController] = None
def get_controller() -> ExecutionController:
    global _controller
    if _controller is None: _controller = ExecutionController()
    return _controller

_original_acompletion = litellm.acompletion

# --- AUDITED & IMPROVED COMPONENTS ---

class Guardrail:
    @staticmethod
    def sanitize(query: str) -> str:
        forbidden = ["ignore previous instructions", "system prompt", "delete all", "drop database"]
        clean_query = query.strip()
        for pattern in forbidden:
            if pattern in clean_query.lower():
                raise ValueError(f"Security Policy Violation: Query contains forbidden logic.")
        return clean_query

class FewShotLibrary:
    EXAMPLES = {
        "Aggregation": [
            {"q": "How many users joined since 2024?", "sql": "SELECT COUNT(*) FROM users WHERE created_at >= '2024-01-01';"},
            {"q": "Top products by stock", "sql": "SELECT name, stock FROM products ORDER BY stock DESC LIMIT 5;"}
        ],
        "Join": [
            {"q": "List products with their category names", "sql": "SELECT p.name, c.name as category FROM products p JOIN categories c ON p.category_id = c.id;"},
            {"q": "Total stock per category", "sql": "SELECT c.name, SUM(p.stock) FROM categories c JOIN products p ON c.id = p.category_id GROUP BY 1;"}
        ]
    }

    @classmethod
    def get_examples(cls, category: str) -> str:
        examples = cls.EXAMPLES.get(category, cls.EXAMPLES["Aggregation"])
        return "\n".join([f"Prompt: \"{ex['q']}\"\nResponse SQL: {ex['sql']}\n" for ex in examples[:2]])

class QueryClassifier:
    def __init__(self, controller: ExecutionController):
        self.controller = controller

    async def classify(self, query: str) -> Dict[str, str]:
        prompt = f"Analyze: \"{query}\"\nReturn JSON: {{\"intent\": \"GENERAL/DATA/HYBRID\", \"complexity\": \"LOW/HIGH\"}}"
        res = await self.controller.execute_task([{"role": "user", "content": prompt}], preferred_model=os.getenv("GEMINI_LITE"))
        try:
            match = re.search(r'\{.*\}', res["content"], re.DOTALL)
            data = json.loads(match.group(0)) if match else {"intent": "GENERAL", "complexity": "LOW"}
            return {"intent": data.get("intent", "GENERAL").upper(), "complexity": data.get("complexity", "LOW").upper()}
        except:
            return {"intent": "GENERAL", "complexity": "LOW"}

class AssistantPromptBuilder:
    def __init__(self, dialect: str = "PostgreSQL"):
        self.dialect = dialect

    def build(self, query: str, schema: str, history: str, intent: str, error_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        system = f"""You are a Premium AI Senior Data Partner and Expert Analyst.
Your tone is professional, understanding, and deeply analytical.
Analyze the user's request with empathy and context. Explain 'why' certain data points matter. 

CONSTRAINTS:
- Use professional, encouraging language.
- Explain your findings in a narrative way before providing tech details.
- ALWAYS return valid JSON at the end.

Output Structure:
{{
  "type": "summary|data|analysis|hybrid",
  "title": "A professional title for this insight",
  "explanation": "Markdown description with professional tone",
  "sql": "SQL code here",
  "sections": [{{"title": "Section Title", "content": "Detailed professional analysis"}}],
  "insights": ["Pro Insight 1", "Pro Insight 2"],
  "meta": {{"complexity": "..."}}
}}

SCHEMA: {schema}
HISTORY: {history}
INTENT: {intent}
{f"CRITICAL: Fix previous error: {error_context}" if error_context else ""}"""

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": query}
        ]

class LLMEngine:
    def __init__(self):
        self.controller = get_controller()
        self.classifier = QueryClassifier(self.controller)
        self.builder = AssistantPromptBuilder()

    async def generate_response(self, user_query: str, schema_context: str, history_context: str, error_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            clean_query = Guardrail.sanitize(user_query)
        except ValueError as e:
            return {"intent": "GENERAL", "explanation": str(e), "sql": None, "error": str(e)}

        classification = await self.classifier.classify(clean_query)
        intent = classification["intent"]
        complexity = classification["complexity"]
        
        messages = self.builder.build(clean_query, schema_context, history_context, intent, error_context=error_context)
        
        logger.info(f"LLM Engine: Handling intent '{intent}' (Complexity: {complexity})...")
        res = await self.controller.execute_task(messages, preferred_model=os.getenv("GEMINI_FLASH"))
        
        if res.get("error"):
            return {"intent": intent, "complexity": complexity, "explanation": "System error.", "sql": None, "error": res["error"]}

        parsed_result = self._parse_json(res["content"])
        return {
            "intent": intent,
            "complexity": complexity,
            **parsed_result,
            "model": res.get("model")
        }

    async def generate_stream(self, user_query: str, schema_context: str, history_context: str) -> AsyncGenerator[str, None]:
        """
        New streaming method for real-time interaction.
        """
        classification = await self.classifier.classify(user_query)
        intent = classification["intent"]
        messages = self.builder.build(user_query, schema_context, history_context, intent)
        
        model = os.getenv("GEMINI_FLASH")
        async for chunk in self.controller._call_llm_stream(messages, model):
            yield chunk

    def _parse_json(self, raw_response: str) -> Dict[str, Any]:
        try:
            match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return {
                    "type": data.get("type", "summary"),
                    "title": data.get("title", data.get("heading")),
                    "explanation": data.get("explanation", data.get("content", "")),
                    "sections": data.get("sections", []),
                    "sql": data.get("sql"),
                    "insights": data.get("insights", []),
                    "examples": data.get("examples", [])
                }
        except Exception:
             pass
        return {"explanation": raw_response}
