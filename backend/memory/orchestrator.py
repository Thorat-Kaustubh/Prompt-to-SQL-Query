from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from memory.semantic import SemanticMemory

class MemoryOrchestrator:
    """
    Memory Orchestrator Service (CRITICAL).
    Coordinates Layer 1 (ST), Layer 2 (LT), and Layer 3 (Semantic) Memory.
    
    1. Decide what to store:
       - All queries in long-term memory
       - Embeddings for meaningful queries only
       - Avoid storing noise (trivial inputs)

    2. Decide what to retrieve:
       - Always fetch short-term memory
       - Optionally fetch semantic matches (top-k)
       - Merge context intelligently

    3. Optimize prompt context:
       - Limit token usage
       - Remove redundant history
       - Prioritize relevant context
    """
    def __init__(self, user_id: str):
        self.user_id = user_id
        # RBAC: user_id is passed during initialization and enforced in all methods
        
        self.st_memory = ShortTermMemory(limit=5)
        self.lt_memory = LongTermMemory()
        self.semantic_memory = SemanticMemory()

    def get_full_context(self, current_query: str, include_semantic: bool = True) -> str:
        """
        Retrieves context and formats it for LLM prompt injection.
        """
        # 1. Fetch short-term memory (last 3-5 queries)
        st_history = self.st_memory.get_history(self.user_id)
        
        # 2. Perform semantic search (top k similarity search)
        semantic_matches = []
        if include_semantic:
            semantic_matches = self.semantic_memory.query_interactions(
                self.user_id, 
                current_query, 
                top_k=3
            )
            
        return self._merge_and_optimize_context(st_history, semantic_matches)

    def store_interaction(self, query: str, response: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Sync interaction to all memory layers.
        """
        # Store in Long-Term Memory (Persistent/Full Log)
        self.lt_memory.store_interaction(self.user_id, query, response, metadata)
        
        # Update Short-Term Memory (Fast Context)
        self.st_memory.add_interaction(self.user_id, {"query": query, "response": response})
        
        # Semantic storage (Embeddings) - filter trivial inputs to avoid noise
        if len(query.strip()) > 10:  # Threshold for 'meaningful' interaction
            self.semantic_memory.store_interaction(self.user_id, query, response)

    def _merge_and_optimize_context(self, st_history: List[Dict], semantic_history: List[Dict]) -> str:
        """
        Merge and deduplicate history to optimize for the LLM token budget.
        """
        context_parts = []
        seen_queries = set()

        # Prioritize Short-Term Memory for conversational flow
        if st_history:
            context_parts.append("--- RECENT CONVERSATION HISTORY ---")
            for entry in st_history:
                context_parts.append(f"User: {entry['query']}\nAI: {entry['response']}")
                seen_queries.add(entry['query'].lower().strip())

        # Include Semantic Memory for relevant context (excluding duplicates)
        if semantic_history:
            found_relevant = False
            for entry in semantic_history:
                if entry['query'].lower().strip() not in seen_queries:
                    if not found_relevant:
                        context_parts.append("\n--- RELEVANT PAST INTERACTIONS ---")
                        found_relevant = True
                    context_parts.append(f"User: {entry['query']}\nAI: {entry['response']}")
        
        return "\n".join(context_parts)

    def clear_all_memory(self):
        """
        Wipe all memory layers for this user.
        """
        self.st_memory.clear(self.user_id)
        self.lt_memory.clear(self.user_id)
        self.semantic_memory.clear(self.user_id)
        logger.info(f"Successfully cleared all memory for user: {self.user_id}")
