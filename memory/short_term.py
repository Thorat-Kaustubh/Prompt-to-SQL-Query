import redis
import json
from typing import List, Dict, Any, Optional
import os
from loguru import logger

class ShortTermMemory:
    """
    Short-Term Memory Manager (Layer 1).
    Stores the last 3–5 interactions per user for immediate conversational context.
    Uses Redis as the primary cache, falls back to in-memory dictionary if Redis is unavailable.
    """
    def __init__(self, limit: int = 5, redis_url: Optional[str] = None):
        self.limit = limit
        self.redis_client = None
        self._in_memory_cache: Dict[str, List[Dict[str, Any]]] = {}

        # Initialize Redis if URL is provided
        url = redis_url or os.getenv("REDIS_URL")
        if url:
            try:
                self.redis_client = redis.from_url(url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                logger.info("Connected to Redis for Short-Term Memory.")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Falling back to in-memory cache.")
                self.redis_client = None

    def add_interaction(self, user_id: str, interaction: Dict[str, Any]):
        """
        Store a new interaction. Automatically prunes old ones.
        """
        if self.redis_client:
            try:
                key = f"stm:{user_id}"
                # Fetch existing history
                history_json = self.redis_client.get(key)
                history = json.loads(history_json) if history_json else []
                
                # Add new interaction and prune
                history.append(interaction)
                history = history[-self.limit:]
                
                # Update Redis
                self.redis_client.set(key, json.dumps(history), ex=3600)  # Expires in 1 hour
                return
            except Exception as e:
                logger.error(f"Short-Term Memory (Redis): Save failed ({str(e)}). Using in-memory fallback.")
                # Don't return, fall through to in-memory
        
        # Fallback to in-memory cache
        if user_id not in self._in_memory_cache:
            self._in_memory_cache[user_id] = []
        
        self._in_memory_cache[user_id].append(interaction)
        self._in_memory_cache[user_id] = self._in_memory_cache[user_id][-self.limit:]

    def get_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve the last 3-5 interactions for the user.
        """
        if self.redis_client:
            try:
                key = f"stm:{user_id}"
                history_json = self.redis_client.get(key)
                return json.loads(history_json) if history_json else []
            except Exception as e:
                logger.error(f"Short-Term Memory (Redis): Retrieval failed ({str(e)}). Using in-memory fallback.")
        
        return self._in_memory_cache.get(user_id, [])

    def clear(self, user_id: str):
        """
        Manual clear for sessions or tests.
        """
        if self.redis_client:
            self.redis_client.delete(f"stm:{user_id}")
        else:
            if user_id in self._in_memory_cache:
                del self._in_memory_cache[user_id]
