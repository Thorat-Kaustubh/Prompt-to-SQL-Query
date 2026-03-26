import os
import re
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
from loguru import logger

# Import SQLValidator to synchronize schema definitions
from validator.engine import SQLValidator

class SemanticTranslator:
    """
    SEMANTIC TRANSLATION LAYER (semantic/) - Senior AI Systems Architect
    - Maps natural language intent to database schema.
    - Auditor-Fixes applied: Schema Sync, Phrase-Order Matching, Detailed Logging.
    """

    def __init__(self, db_path: str = "./semantic_store"):
        # 1. Initialize Dictionary Mapping
        # CRITICAL FIX: Aligned 'users' mapping with actual schema table name.
        # HIGH PRIORITY FIX: Expanded synonyms to handle basic stemming (signed, signing).
        self.dictionary = {
            "total revenue": {"expression": "SUM(orders.amount)", "tables": ["orders"], "synonyms": ["total income", "gross sales"]},
            "revenue": {"expression": "SUM(orders.amount)", "tables": ["orders"], "synonyms": ["income", "sales", "revenue"]},
            "signups": {"expression": "COUNT(users.id)", "tables": ["users"], "synonyms": ["registrations", "new users", "signed up", "signing up", "signup"]},
            "users": {"expression": "users", "tables": ["users"], "synonyms": ["clients", "people", "members", "accounts"]},
            "products": {"expression": "products", "tables": ["products"], "synonyms": ["items", "stock", "inventory", "goods"]},
            "average price": {"expression": "AVG(products.price)", "tables": ["products"], "synonyms": ["mean cost", "avg price"]}
        }
        
        # 2. Initialize ChromaDB
        try:
            self.chroma_client = chromadb.PersistentClient(path=db_path)
            self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
            self.collection = self.chroma_client.get_or_create_collection(
                name="schema_semantics",
                embedding_function=self.embedding_fn
            )
            # CRITICAL FIX: Synchronize with SQLValidator.ALLOWED_SCHEMA
            self._sync_with_schema()
            self.embedding_enabled = True
            logger.info("Semantic Search: Ready.")
        except Exception as e:
            logger.error(f"Semantic Search: Error initializing: {str(e)}")
            self.embedding_enabled = False

    def _sync_with_schema(self):
        """
        CRITICAL FIX: Automatically seeds the vector store from the SQLValidator source of truth.
        """
        schema = SQLValidator.ALLOWED_SCHEMA
        definitions = []
        
        for table, columns in schema.items():
            # Table Metadata
            definitions.append({
                "id": f"table_{table}",
                "text": f"Database table {table}. Use this for queries about {table}.",
                "metadata": {"type": "table", "name": table}
            })
            # Column Metadata
            for col in columns:
                definitions.append({
                    "id": f"col_{table}_{col}",
                    "text": f"Column {col} in table {table}. Represents {col.replace('_', ' ')}.",
                    "metadata": {"type": "column", "table": table, "name": col}
                })
        
        for item in definitions:
            self.collection.upsert(
                ids=[item["id"]],
                documents=[item["text"]],
                metadatas=[item["metadata"]]
            )

    def translate(self, user_query: str) -> Dict[str, Any]:
        """
        The core flow: Normalize -> Phrase-Ordered Mapping -> Semantic Search -> Detail Logging.
        """
        normalized_query = user_query.lower()
        resolved_mappings = []
        
        # HIGH PRIORITY FIX: Sort dictionary by key length (descending) to match longest phrases first.
        # This prevents "total revenue" being split into "total" and "revenue".
        sorted_terms = sorted(self.dictionary.keys(), key=len, reverse=True)
        
        temp_query = normalized_query
        for term in sorted_terms:
            info = self.dictionary[term]
            # Match the term or any of its synonyms
            match_found = False
            if term in temp_query:
                match_found = True
                matched_text = term
            else:
                for syn in info["synonyms"]:
                    if syn in temp_query:
                        match_found = True
                        matched_text = syn
                        break
            
            if match_found:
                resolved_mappings.append({
                    "term": term,
                    "matched_text": matched_text,
                    "resolved": info["expression"],
                    "tables": info["tables"],
                    "source": "dictionary"
                })
                # Remove matched part to prevent redundant sub-matching
                temp_query = temp_query.replace(matched_text, " [RESOLVED] ")
                logger.info(f"Semantic Layer [DICT MATCH]: '{matched_text}' -> '{term}' -> {info['expression']}")

        # 2. SEMANTIC VECTOR SEARCH
        semantic_matches = []
        if self.embedding_enabled:
            try:
                results = self.collection.query(
                    query_texts=[user_query],
                    n_results=3
                )
                
                if results["metadatas"] and results["metadatas"][0]:
                    for i, meta in enumerate(results["metadatas"][0]):
                        distance = results["distances"][0][i]
                        confidence = 1.0 / (1.0 + distance) 
                        
                        if confidence > 0.4: # Low-bar threshold for suggestions
                            semantic_matches.append({
                                "name": meta.get("name"),
                                "type": meta.get("type"),
                                "table": meta.get("table", ""),
                                "confidence": round(confidence, 2),
                                "description": results["documents"][0][i]
                            })
                            logger.info(f"Semantic Layer [VECTOR MATCH]: '{meta.get('name')}' ({meta.get('type')}) with confidence {round(confidence, 2)}")
            except Exception as e:
                logger.warning(f"Semantic Search Error: {str(e)}")

        # 3. BUILD PROMPT CONTEXT
        context_block = self._generate_prompt_context(resolved_mappings, semantic_matches)
        
        return {
            "original_query": user_query,
            "resolved_mappings": resolved_mappings,
            "semantic_matches": semantic_matches,
            "semantic_context": context_block
        }

    def _generate_prompt_context(self, mappings: List[Dict], suggestions: List[Dict]) -> str:
        """
        Formats semantic insights into a context block, prioritizing high-confidence matches.
        """
        lines = ["### SEMANTIC CONTEXT & BUSINESS RULES"]
        
        if mappings:
            lines.append("Confirmed Business Terminology:")
            for m in mappings:
                lines.append(f"- '{m['matched_text']}' identified as business concept '{m['term']}'. SQL requirement: {m['resolved']}")
        
        if suggestions:
            # Only suggest things with decent confidence that weren't already resolved
            high_conf = [s for s in suggestions if s["confidence"] > 0.5]
            if high_conf:
                lines.append("\nPotential Schema Matches (Likely Relevant):")
                for s in high_conf:
                    target = f"{s['table']}.{s['name']}" if s['type'] == 'column' else s['name']
                    lines.append(f"- {s['type'].title()}: {target} (Context: {s['description']})")
        
        return "\n".join(lines) if len(lines) > 1 else ""

if __name__ == "__main__":
    # Test execution
    translator = SemanticTranslator()
    res = translator.translate("Show me the total revenue from people who signed up last week")
    print(res["semantic_context"])
