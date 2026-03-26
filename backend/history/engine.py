import os
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from loguru import logger
import uuid

class HistoryEngine:
    """
    HISTORY ENGINE (history/)
    - Manages persistence for conversations and messages in Supabase.
    - Uses Service Role for administrative persistence to ensure chat logs are saved reliably.
    """
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.supabase: Client = create_client(self.url, self.key)

    def get_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            res = self.supabase.table("conversations")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("last_message_at", desc=True)\
                .execute()
            return res.data
        except Exception as e:
            logger.error(f"History Engine: Failed to fetch conversations: {e}")
            return []

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        try:
            res = self.supabase.table("messages")\
                .select("*")\
                .eq("conversation_id", conversation_id)\
                .order("created_at", desc=False)\
                .execute()
            return res.data
        except Exception as e:
            logger.error(f"History Engine: Failed to fetch messages: {e}")
            return []

    def create_conversation(self, user_id: str, title: str = "New Chat") -> str:
        try:
            res = self.supabase.table("conversations")\
                .insert({"user_id": user_id, "title": title})\
                .execute()
            if res.data:
                return res.data[0]["id"]
            return None
        except Exception as e:
            logger.error(f"History Engine: Failed to create conversation: {e}")
            return None

    def save_message(self, conversation_id: str, role: str, content: str, data: Optional[Dict[str, Any]] = None):
        try:
            # 1. Save Message
            self.supabase.table("messages").insert({
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "data": data
            }).execute()
            
            # 2. Update conversation timestamp
            self.supabase.table("conversations").update({
                "last_message_at": "now()"
            }).eq("id", conversation_id).execute()
            
        except Exception as e:
            logger.error(f"History Engine: Failed to save message: {e}")

    def delete_conversation(self, conversation_id: str):
        try:
            self.supabase.table("conversations").delete().eq("id", conversation_id).execute()
        except Exception as e:
            logger.error(f"History Engine: Failed to delete conversation: {e}")

    def update_conversation(self, conversation_id: str, updates: Dict[str, Any]):
        try:
            self.supabase.table("conversations").update(updates).eq("id", conversation_id).execute()
        except Exception as e:
            logger.error(f"History Engine: Failed to update conversation: {e}")
