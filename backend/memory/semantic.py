import chromadb
from chromadb.config import Settings
from google import genai
import os
import uuid
from typing import List, Dict, Any, Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class SemanticMemory:
    """
    NATIVE Semantic Memory Engine (Layer 3 - High Availability).
    Uses the modern Google GenAI SDK (google-genai) for future-proof stability.
    Fallback: gemini-embedding-2-preview -> gemini-embedding-001
    """
    def __init__(self, collection_name: Optional[str] = None):
        host = os.getenv("CHROMA_HOST")
        api_key = os.getenv("CHROMA_API_KEY")
        tenant = os.getenv("CHROMA_TENANT", "default")
        db = os.getenv("CHROMA_DATABASE", "default")
        coll_name = collection_name or os.getenv("CHROMA_COLLECTION", "conversations")
        
        # Configure Gemini Native for embeddings (New SDK Style)
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            self.genai_client = genai.Client(api_key=gemini_key)
        else:
            self.genai_client = None
            logger.warning("Semantic Memory: GEMINI_API_KEY missing. Embeddings will fail.")

        if not host or not api_key:
            logger.info("ChromaDB: No remote credentials. Using local storage mode.")
            try:
                persist_path = os.path.join(os.path.expanduser("~"), ".chroma_data")
                os.makedirs(persist_path, exist_ok=True)
                self.client = chromadb.PersistentClient(path=persist_path)
            except Exception as e:
                logger.info(f"Local ChromaDB access limited ({e}). Falling back to ephemeral memory.")
                self.client = chromadb.Client()
        else:
            try:
                self.client = chromadb.HttpClient(
                    host=host,
                    headers={"Authorization": f"Bearer {api_key}"},
                    tenant=tenant,
                    database=db
                )
            except Exception as e:
                logger.info(f"ChromaDB connection failed ({e}). Falling back to In-Memory.")
                self.client = chromadb.Client()

        try:
            self.collection = self.client.get_or_create_collection(name=coll_name)
        except Exception as e:
            logger.error(f"Error initializing ChromaDB collection: {e}")
            self.collection = None

    def _get_embedding_values(self, response: Any) -> List[float]:
        """Robustly extracts embedding values from different SDK versions."""
        # Check singular 'embedding' property (SDK v1 common)
        if hasattr(response, 'embedding') and response.embedding:
            return response.embedding.values
        # Check plural 'embeddings' list (SDK v1 batches or older previews)
        if hasattr(response, 'embeddings') and len(response.embeddings) > 0:
            return response.embeddings[0].values
        return []

    def _generate_embedding(self, text: str) -> List[float]:
        if not self.genai_client: return []

        primary_model = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-2-preview")
        backup_model = "models/gemini-embedding-001" # Verified name in models_list.txt
        
        p_model = primary_model.replace("gemini/", "").replace("models/", "")
        if not p_model.startswith("models/"): p_model = f"models/{p_model}"

        try:
            response = self.genai_client.models.embed_content(
                model=p_model,
                contents=text,
                config={"task_type": "RETRIEVAL_DOCUMENT"}
            )
            return self._get_embedding_values(response)
        except Exception as e:
            logger.warning(f"Memory: Primary Embedding Failed ({e}). Trying backup {backup_model}...")
            try:
                response = self.genai_client.models.embed_content(
                    model=backup_model,
                    contents=text,
                    config={"task_type": "RETRIEVAL_DOCUMENT"}
                )
                return self._get_embedding_values(response)
            except Exception as backup_e:
                logger.error(f"Memory: Critical Embedding Failure - {backup_e}")
                return []

    def store_interaction(self, user_id: str, query: str, response: str):
        if not self.collection: return
        vector = self._generate_embedding(f"Q: {query}\nA: {response}")
        if not vector: return
        try:
            self.collection.add(
                ids=[str(uuid.uuid4())],
                embeddings=[vector],
                metadatas=[{"user_id": user_id, "query": query, "response": response}],
                documents=[f"{query} {response}"]
            )
        except Exception as e:
            logger.error(f"Error adding to semantic memory: {e}")

    def query_interactions(self, user_id: str, search_query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if not self.collection: return []
        vector = self._generate_embedding(search_query)
        if not vector: return []
        try:
            results = self.collection.query(
                query_embeddings=[vector],
                n_results=top_k,
                where={"user_id": user_id}
            )
            interactions = []
            if results and results.get("metadatas"):
                for meta_list in results["metadatas"]:
                    for meta in meta_list:
                        interactions.append(meta)
            return interactions
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def clear(self, user_id: str):
        if not self.collection: return
        try:
            self.collection.delete(where={"user_id": user_id})
        except Exception as e:
            logger.error(f"Error clearing user semantic memory: {e}")
