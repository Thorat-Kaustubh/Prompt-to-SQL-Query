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
    Fallback: gemini-embedding-2-preview -> text-embedding-004
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
            logger.warning("ChromaDB credentials missing. Attempting persistent local storage.")
            try:
                # Use a home-directory path for better cross-platform permission stability
                persist_path = os.path.join(os.path.expanduser("~"), ".chroma_data")
                os.makedirs(persist_path, exist_ok=True)
                self.client = chromadb.PersistentClient(path=persist_path)
                logger.info(f"Connected to local persistent ChromaDB at {persist_path}.")
            except Exception as e:
                logger.error(f"Local persistence failed ({e}). Using In-Memory ephemeral storage.")
                self.client = chromadb.Client()
        else:
            try:
                # HttpClient setup for hosted Chroma
                self.client = chromadb.HttpClient(
                    host=host,
                    headers={"Authorization": f"Bearer {api_key}"},
                    tenant=tenant,
                    database=db
                )
                logger.info(f"Connected to ChromaDB (host: {host}).")
            except Exception as e:
                logger.error(f"Failed to connect to primary ChromaDB: {e}. Falling back to In-Memory.")
                self.client = chromadb.Client()

        try:
            self.collection = self.client.get_or_create_collection(name=coll_name)
        except Exception as e:
            logger.error(f"Error initializing ChromaDB collection: {e}")
            self.collection = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _generate_embedding(self, text: str) -> List[float]:
        """
        New SDK Embedding Generation with Dual-Tier Fallback.
        """
        if not self.genai_client:
            return []

        primary_model = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
        backup_model = "text-embedding-004"
        
        # New SDK model names don't necessarily need 'models/' prefix but support it
        p_model = primary_model.replace("gemini/", "").replace("models/", "")
        
        try:
            logger.info(f"Memory: Generating embedding with {p_model}")
            # New SDK format: client.models.embed
            response = self.genai_client.models.embed(
                model=p_model,
                contents=text,
                config={"task_type": "RETRIEVAL_DOCUMENT"}
            )
            # Response structure is list-based in new SDK
            return response.embeddings[0].values
        except Exception as e:
            logger.warning(f"Memory: Primary Embedding Failed ({e}). Falling back.")
            try:
                response = self.genai_client.models.embed(
                    model=backup_model,
                    contents=text,
                    config={"task_type": "RETRIEVAL_DOCUMENT"}
                )
                return response.embeddings[0].values
            except Exception as backup_e:
                logger.error(f"Memory: Critical Embedding Failure: {backup_e}")
                return []

    def store_interaction(self, user_id: str, query: str, response: str):
        if not self.collection: return
        if len(query.strip()) < 5: return

        text = f"Query: {query}\nResponse: {response}"
        vector = self._generate_embedding(text)
        
        if not vector: return

        try:
            self.collection.add(
                ids=[str(uuid.uuid4())],
                embeddings=[vector],
                metadatas=[{"user_id": user_id, "query": query, "response": response}],
                documents=[text]
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
