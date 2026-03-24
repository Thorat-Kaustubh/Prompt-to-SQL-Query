from typing import List, Dict, Any, Optional
from memory.orchestrator import MemoryOrchestrator
from loguru import logger

class MemoryEngine:
    """
    Memory Engine (Phase 3 - Multi-Layered Memory).
    Enforces a three-layer memory architecture:
    1. Short-term (Redis/Cache)
    2. Long-term (Supabase)
    3. Semantic (ChromaDB Vector DB)
    
    All logic is encapsulated within the memory module.
    Enforces RBAC by strictly requiring user_id for all operations.
    """
    def __init__(self, user_id: str):
        if not user_id:
            logger.error("User ID is required for memory operations (RBAC).")
            # In a real system, you might raise an Exception here.
        self.orchestrator = MemoryOrchestrator(user_id=user_id)

    def get_context(self, current_query: str) -> str:
        """
        Pull conversational context for prompt injection.
        Retrieves last few interactions and semantic matches.
        """
        return self.orchestrator.get_full_context(current_query)

    def add_interaction(self, query: str, response: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Save interaction across all memory layers (LT, ST, Semantic).
        """
        self.orchestrator.store_interaction(query, response, metadata)

    def clear(self):
        """
        Clear all user history (all layers).
        """
        self.orchestrator.clear_all_memory()

if __name__ == "__main__":
    # Test memory engine locally (Ensure valid keys in .env)
    mock_user = "test-user-123"
    engine = MemoryEngine(user_id=mock_user)
    
    print(f"Initial context: {engine.get_context('How many people live in New York?')}")
    
    engine.add_interaction(
        query="How many people live in New York?",
        response="There are approximately 8.3 million people living in New York City."
    )
    
    print(f"Context after interaction: {engine.get_context('What about London?')}")

