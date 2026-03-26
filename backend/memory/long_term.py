import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from loguru import logger

class LongTermMemory:
    """
    Long-Term Memory Manager (Layer 2).
    Stores full query history in Supabase (PostgreSQL).
    Each entry is tied to a user_id for RBAC.
    """
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        url = supabase_url or os.getenv("SUPABASE_URL")
        key = supabase_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Use Service Role for backend ops

        if not url or not key:
            logger.error("Supabase credentials missing. Long-Term Memory will not persist.")
            self.client = None
        else:
            try:
                self.client: Client = create_client(url, key)
                logger.info("History: connected.")
            except Exception as e:
                logger.error(f"Failed to connect to Supabase: {e}")
                self.client = None

    def store_interaction(self, user_id: str, query: str, response: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Persist query + response in the memory_logs table.
        """
        if not self.client:
            logger.warning("Supabase client not initialized. Cannot store interaction.")
            return
        
        entry = {
            "user_id": user_id,
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        try:
            # Assumes table 'memory_logs' exists
            # Every entry is tied to user_id for RBAC enforcement at database level (RLS)
            self.client.table("memory_logs").insert(entry).execute()
        except Exception as e:
            logger.error(f"Failed to persist interaction to Supabase: {e}")

    def fetch_user_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve history for a specific user.
        RBAC: This only pulls records for the given user_id.
        """
        if not self.client:
            return []

        try:
            response = self.client.table("memory_logs")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching historical memory: {e}")
            return []

    def clear(self, user_id: str):
        """
        Delete all logs for a user (useful for GDPR / privacy compliance).
        """
        if not self.client: return
        try:
            self.client.table("memory_logs").delete().eq("user_id", user_id).execute()
        except Exception as e:
            logger.error(f"Error clearing user memory: {e}")
