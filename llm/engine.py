import os
import asyncio
import time
from typing import Optional, Dict, Any, List
from loguru import logger
import litellm
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configuration for Execution Controller
CONCURRENCY_LIMITS = {
    "gemini": 2,      # Stricter for Gemini
    "groq": 5,        # Smoothed for Groq to avoid bursts
}

MODEL_FALLBACK_CHAIN = [
    os.getenv("GEMINI_LITE", "gemini/gemini-2.0-flash-lite"),
    os.getenv("GEMINI_FLASH", "gemini/gemini-2.0-flash"),
    os.getenv("GROQ_LLAMA_8B", "groq/llama-3.1-8b-instant"),
    os.getenv("GROQ_LLAMA_70B", "groq/llama-3.3-70b-versatile")
]

class ExecutionController:
    """
    AI EXECUTION CONTROLLER (llm/engine.py)
    - Manages all LLM calls with Rate Limiting, Concurrency, and Fallbacks.
    - Protects the system from provider failures and rate limits.
    """
    def __init__(self):
        self._semaphores_instance = None
        self.output_history = []
        # Circuit Breaker state (timestamp of next allowed call)
        self._circuit_breakers = {
            "gemini": 0,
            "groq": 0
        }
        # Multi-provider failure counters
        self._failure_counts = {
            "gemini": 0,
            "groq": 0
        }
        # LiteLLM allows us to use multiple providers with a unified API
        litellm.telemetry = False 

    @property
    def _semaphores(self):
        if self._semaphores_instance is None:
            # We initialize semaphores here safely within the running loop
            self._semaphores_instance = {
                "gemini": asyncio.Semaphore(CONCURRENCY_LIMITS["gemini"]),
                "groq": asyncio.Semaphore(CONCURRENCY_LIMITS["groq"])
            }
        return self._semaphores_instance
        
    async def _call_llm(self, prompt: str, model: str, priority: str = "medium", metadata: Dict[str, Any] = None) -> str:
        """
        Internal LLM call with Concurrency, Circuit Breaker, and Observability.
        """
        provider = "gemini" if "gemini" in model.lower() else "groq"
        
        if time.time() < self._circuit_breakers[provider]:
            logger.warning(f"Circuit Breaker: [OFF] {provider} is cooling down. Rejecting request.")
            raise Exception(f"Circuit Breaker active for {provider}")

        # 2. Priority Delay Adjustment
        if priority == "low":
            await asyncio.sleep(0.5) # Throttle low priority

        sems = self._semaphores
        semaphore = sems.get(provider, sems["gemini"])

        async with semaphore:
            task_id = (metadata or {}).get("task_id", "unknown")
            logger.info(f"Execution Controller: [EXEC] [{priority.upper()}] Executing {model} (Task: {task_id})")
            
            # Explicit retry loop for 429 Rate Limits
            max_attempts = 4
            backoff = 2 # Starting backoff
            
            for attempt in range(max_attempts):
                start_time = time.time()
                try:
                    # Use _original_acompletion to bypass interceptor recursion
                    response = await _original_acompletion(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1
                    )
                    latency = (time.time() - start_time) * 1000
                    
                    content = response.choices[0].message.content
                    if not content:
                        raise ValueError("Empty response from LLM")
                        
                    # Reset failure count on success
                    self._failure_counts[provider] = 0
                    logger.info(f"Execution Controller: [DONE] {model} Success ({latency:.2f}ms)")
                    return content

                except Exception as e:
                    # Detect 429 or Rate Limit specifically
                    err_str = str(e).lower()
                    if "429" in err_str or "rate" in err_str:
                        if attempt < max_attempts - 1:
                            wait_time = backoff * (attempt + 1)
                            logger.warning(f"Execution Controller: [WAIT] Rate Limit Hit on {model}. Waiting {wait_time}s... (Attempt {attempt+1}/{max_attempts})")
                            await asyncio.sleep(wait_time)
                            continue
                    
                    # Original Failure logic
                    self._failure_counts[provider] += 1
                    if self._failure_counts[provider] >= 3:
                         cooldown = 60 # 60 seconds (as per instructions)
                         self._circuit_breakers[provider] = time.time() + cooldown
                         logger.error(f"Circuit Breaker: [TRIP] Tripping {provider} for {cooldown}s.")
                    raise e

    async def execute_task(self, prompt: str, preferred_model: Optional[str] = None, priority: str = "medium", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main entry point for task execution with robust management.
        """
        start_idx = 0
        if preferred_model:
            try:
                start_idx = MODEL_FALLBACK_CHAIN.index(preferred_model)
            except ValueError:
                start_idx = 0

        # Iterate through fallback chain
        for i in range(start_idx, len(MODEL_FALLBACK_CHAIN)):
            current_model = MODEL_FALLBACK_CHAIN[i]
            try:
                result = await self._call_llm(prompt, current_model, priority, metadata)
                return {
                    "content": result,
                    "model": current_model,
                    "error": None,
                    "latency": 0 # Tracked in logs
                }
            except Exception as e:
                logger.error(f"Execution Controller: ⚠️ {current_model} failed: {str(e)}")
                if i == len(MODEL_FALLBACK_CHAIN) - 1:
                    return {"content": "", "model": current_model, "error": f"Chain Exhaustion: {str(e)}"}
                logger.info(f"Execution Controller: 🔄 Falling back...")

        return {"content": "", "error": "No models available."}

# Lazy Singleton instance of the controller
_controller: Optional[ExecutionController] = None

def get_controller() -> ExecutionController:
    global _controller
    if _controller is None:
        _controller = ExecutionController()
    return _controller

# --- GLOBAL INTERCEPTOR (Rate Limit & Tool Compatibility Solution) ---
# We monkeypatch litellm to ensure ALL calls (including from CrewAI/LangChain)
# pass through our Execution Controller's semaphores and retry logic.

_original_acompletion = litellm.acompletion
_original_completion = litellm.completion

async def intercepted_acompletion(*args, **kwargs):
    model = kwargs.get("model", "")
    messages = kwargs.get("messages", [])
    tools = kwargs.get("tools")
    prompt = messages[-1]["content"] if messages else ""
    
    # 🎯 REMOVE TIMEOUT: As requested by USER
    kwargs.pop("request_timeout", None)
    kwargs["request_timeout"] = 600 # 10 minute safety limit instead of None if needed, but we prefer "infinity"
    
    preferred = model
    if tools and "groq" in model.lower():
         logger.info(f"Interceptor: ⚡ Tool-Calling detected on Groq. Re-routing to Gemini for stability.")
         preferred = os.getenv("GEMINI_FLASH")
    
    ctrl = get_controller()
    logger.info(f"Interceptor: [ASYNC] Directing {preferred} through Global Execution Controller...")
    
    res = await ctrl.execute_task(
        prompt, 
        preferred_model=preferred, 
        metadata={"is_intercepted": True, "original_model": model}
    )
    
    if res.get("error"):
         logger.error(f"Interceptor: Critical Failure: {res['error']}. Forcing fallback to raw call.")
         return await _original_acompletion(*args, **kwargs)
         
    # Return a format litellm expects (Duck Typing the response)
    class InterceptedResponse:
        def __init__(self, content, model_name):
            self.choices = [type('Choice', (), {
                'message': type('Message', (), {'content': content, 'role': 'assistant', 'tool_calls': None})
            })]
            self.model = model_name
            self.usage = type('Usage', (), {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0})
            
    return InterceptedResponse(res["content"], res["model"])

def intercepted_completion(*args, **kwargs):
    """Sync wrapper for the intercepted async logic."""
    # CrewAI often uses the sync call. We bridge it to our async controller.
    # Re-use the async logic to avoid duplication
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # If we are already in an async loop (like FastAPI), we might need a different approach
        # But for CrewAI standalone, this usually works. 
        # For safety, let's just do a direct sync version of the logic if loop is running.
        import nest_asyncio
        nest_asyncio.apply()
        
    return loop.run_until_complete(intercepted_acompletion(*args, **kwargs))

litellm.acompletion = intercepted_acompletion
litellm.completion = intercepted_completion

class LLMEngine:
    """
    Unified LLM Generation Entry Point.
    Uses the Execution Controller to manage calls.
    """
    def __init__(self, model: Optional[str] = None):
        self.preferred_model = model

    async def generate_sql(self, user_query: str, schema_context: str, history_context: str) -> Dict[str, Any]:
        """
        Explicit Routing to Execution Controller.
        Ensures rate-limiting, retries, and fallback tiers are applied.
        """
        prompt = self._build_prompt(user_query, schema_context, history_context)
        pref = self.preferred_model or os.getenv("GEMINI_FLASH")
        
        # Centralized Execution Logic (Get current controller)
        current_controller = get_controller()
        result = await current_controller.execute_task(prompt, preferred_model=pref)
        
        if result.get("error"):
             return {"sql": "", "error": result["error"]}
             
        return {
            "sql": self._cleanse_sql(result["content"]),
            "model": result["model"],
            "error": None
        }

    def _build_prompt(self, query: str, schema: str, history: str) -> str:
        # FEW-SHOT GOLD STANDARD EXAMPLES
        examples = """
        ---
        EXAMPLAR 1: Complex 3-Way Join
        Prompt: "Total revenue per country in 2026"
        Response: {
            "sql": "SELECT c.country_name, SUM(o.total_amount) FROM countries c JOIN users u ON c.id = u.country_id JOIN orders o ON u.id = o.user_id WHERE extract(year from o.order_date) = 2026 GROUP BY 1 LIMIT 50;",
            "explanation": "Calculates total order amounts by joining countries to users and orders, filtering for the year 2026.",
            "complexity": "Medium",
            "suggested_visualization": "Bar Chart",
            "confidence": 0.95
        }
        ---
        """

        return f"""
        ### Task: Convert the following natural language query into valid, secure PostgreSQL.
        ### Response Format: JSON Object with keys: "sql", "explanation", "complexity" (Low/Medium/High), "suggested_visualization" (e.g., Line Chart, Table, Bar Chart), and "confidence" (0.0-1.0).
        
        ### Gold-Standard Examples:
        {examples}

        ### Database Schema Context:
        {schema}

        ### Rules & Guardrails:
        1. Output valid PostgreSQL only.
        2. LIMIT all queries to 50 unless explicitly asked for more.
        3. Never use 'SELECT *'. List columns explicitly.
        4. Join tables using clear aliases.

        ### User Input:
        {query}

        ### Final Output (JSON):
        """

    def _cleanse_sql(self, raw_response: str) -> Dict[str, Any]:
        """
        Parses the enriched JSON response with robust fallbacks.
        """
        import json
        import re
        
        # 1. Attempt strict JSON block extraction
        try:
             json_pattern = r'\{.*\}'
             match = re.search(json_pattern, raw_response, re.DOTALL)
             if match:
                 return json.loads(match.group(0))
        except:
             pass

        # 2. Extract SQL from markdown if JSON fails
        sql_match = re.search(r'```sql\s*(.*?)\s*```', raw_response, re.DOTALL | re.IGNORECASE)
        if not sql_match:
             sql_match = re.search(r'```\s*(.*?)\s*```', raw_response, re.DOTALL)
        
        extracted_sql = sql_match.group(1).strip() if sql_match else raw_response.strip()
        
        # Cleanup common markdown noise
        if extracted_sql.lower().startswith("sql"): 
            extracted_sql = extracted_sql[3:].strip()

        return {
            "sql": extracted_sql,
            "explanation": "Extracted from markdown block (JSON missing).",
            "complexity": "Unknown",
            "suggested_visualization": "Table",
            "confidence": 0.6
        }
