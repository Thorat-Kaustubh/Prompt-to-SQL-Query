import redis
import os
import json
from typing import Optional, Dict, Any
from loguru import logger

class RedisCache:
    """
    Cache Layer (Phase 8).
    Responsible for:
    1. Query -> SQL caching (Phase 8.1.1)
    2. SQL -> Result caching (Phase 8.1.2)
    3. Performance optimization (Benefits listed in Phase 8)
    """
    def __init__(self, redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")):
        self.redis_url = redis_url
        try:
             self.client = redis.from_url(self.redis_url)
             # Explicitly test connection for graceful fallback
             self.client.ping()
             self.enabled = True
             logger.info("Redis Cache: Connected successfully.")
        except Exception as e:
             self.enabled = False
             logger.warning(f"Redis Cache: Connection failed ({str(e)}). Falling back to No-Cache mode.")

    def get_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Check if we already translated or executed this query.
        """
        if not self.enabled:
            return None
            
        try:
             cached_data = self.client.get(f"q_{query}")
             if cached_data:
                  return json.loads(cached_data)
        except:
             return None
        return None

    def set_query(self, query: str, result: Dict[str, Any], ttl: int = 3600):
        """
        Save results or SQL to cache (Phase 8.2).
        """
        if not self.enabled:
            return
            
        try:
             self.client.setex(f"q_{query}", ttl, json.dumps(result))
        except:
             pass

if __name__ == "__main__":
    # Test cache engine locally
    pass
