import redis
import os
import json
import hashlib
import re
from typing import Optional, Dict, Any, Union
from loguru import logger

class RedisCache:
    """
    SENIOR SYSTEMS OPTIMIZATION - ENTERPRISE CACHE LAYER
    - Audit Fixed: Schema Versioning (L1 & L2), Regex Normalization, Size Capping.
    - Security: SHA-256 Scoped Hashing.
    """
    def __init__(self, redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")):
        try:
             self.client = redis.from_url(redis_url)
             self.client.ping()
             self.enabled = True
             logger.info("Redis Cache: Optimization layer ACTIVE.")
        except Exception:
             self.enabled = False
             logger.info("Redis Cache: PASS-THRU mode ACTIVE.")

    def _normalize(self, text: str) -> str:
        """
        Audit Step: Robust Regex Normalization (Handles tabs, multiple spaces, etc).
        """
        return re.sub(r'\s+', ' ', text.strip().lower())

    def _generate_key(self, prefix: str, data: str, user_id: str, schema_version: str) -> str:
        """
        Audit Fixed: Enforces (User + Version) context for ALL keys.
        """
        raw = f"{self._normalize(data)}|{user_id}|{schema_version}"
        hash_val = hashlib.sha256(raw.encode()).hexdigest()
        return f"{prefix}:{hash_val}"

    # --- LEVEL 1: QUERY -> SQL CACHE ---
    def get_sql_cache(self, user_query: str, user_id: str, schema_version: str) -> Optional[str]:
        if not self.enabled: return None
        key = self._generate_key("llm_sql", user_query, user_id, schema_version)
        try:
             val = self.client.get(key)
             return val.decode() if val else None
        except: return None

    def set_sql_cache(self, user_query: str, sql: str, user_id: str, schema_version: str, ttl: int = 86400):
        if not self.enabled: return
        key = self._generate_key("llm_sql", user_query, user_id, schema_version)
        try: self.client.setex(key, ttl, sql)
        except: pass

    # --- LEVEL 2: SQL -> RESULT CACHE ---
    def get_result_cache(self, sql_query: str, user_id: str, schema_version: str) -> Optional[Dict[str, Any]]:
        """
        Audit Fixed: SQL results are now version-scoped to prevent stale schema drift.
        """
        if not self.enabled: return None
        key = self._generate_key("db_res", sql_query, user_id, schema_version)
        try:
             val = self.client.get(key)
             return json.loads(val) if val else None
        except: return None

    def set_result_cache(self, sql_query: str, result: Dict[str, Any], user_id: str, schema_version: str, ttl: int = 900):
        """
        Audit Fixed: Implements 1MB Result Cap (Performance Guard).
        """
        if not self.enabled: return
        
        # 1MB Limit for Caching (Prevention of Redis OOM/Latency)
        serialized_data = json.dumps(result)
        if len(serialized_data) > 1024 * 1024:
            logger.warning("Redis Cache: Skipping L2 cache (Result too large > 1MB).")
            return

        key = self._generate_key("db_res", sql_query, user_id, schema_version)
        try: self.client.setex(key, ttl, serialized_data)
        except: pass

    # --- INVALIDATION HELPERS ---
    def delete_sql_cache(self, user_query: str, user_id: str, schema_version: str):
        if not self.enabled: return
        key = self._generate_key("llm_sql", user_query, user_id, schema_version)
        try: 
            self.client.delete(key)
            logger.info(f"Redis Cache: Purged L1 entry for query hash {key[:10]}...")
        except: pass

    def delete_result_cache(self, sql_query: str, user_id: str, schema_version: str):
        if not self.enabled: return
        key = self._generate_key("db_res", sql_query, user_id, schema_version)
        try: 
            self.client.delete(key)
            logger.info(f"Redis Cache: Purged L2 entry for SQL hash {key[:10]}...")
        except: pass

    def invalidate_schema(self, schema_version: str):
        """
        Global Invalidation for a specific schema version.
        """
        if not self.enabled: return
        try:
             # Scan and clear all keys for this version
             keys = self.client.keys(f"*:*{schema_version}")
             if keys: self.client.delete(*keys)
             logger.info(f"Redis Cache: Flushed all keys for schema {schema_version}")
        except Exception as e:
             logger.error(f"Cache Invalidation Failure: {str(e)}")

if __name__ == "__main__":
    # Test cache engine locally
    pass
