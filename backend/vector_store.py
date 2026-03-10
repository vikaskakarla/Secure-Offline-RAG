import os
import faiss
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Define the model path and vector store path
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_STORE_PATH = "data/vector_store"

# Global cache for the vector store
_CACHED_VECTOR_STORE = None
_CACHED_EMBEDDINGS = None

def get_embeddings():
    """
    Initializes the HuggingFace embeddings model.
    Checks for local cache first to support offline mode.
    """
    global _CACHED_EMBEDDINGS
    if _CACHED_EMBEDDINGS is None:
        print("Loading embeddings model... (This happens once)")
        
        # Check if running offline and model exists locally
        # Default Hugging Face cache structure on Windows
        default_cache_path = os.path.expanduser("~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf")
        
        # Allow override via environment variable
        local_model_path = os.getenv("SENTENCE_TRANSFORMERS_HOME", default_cache_path)

        if os.path.exists(local_model_path):
            print(f"Loading embedding model from local cache: {local_model_path}")
            _CACHED_EMBEDDINGS = HuggingFaceEmbeddings(model_name=local_model_path)
        else:
            print(f"Local model not found at {local_model_path}, attempting download/load from Hub...")
            _CACHED_EMBEDDINGS = HuggingFaceEmbeddings(model_name=MODEL_NAME)
            
    return _CACHED_EMBEDDINGS

def create_vector_store(documents):
    """
    Creates a FAISS vector store from the provided documents and saves it locally.
    """
    embeddings = get_embeddings()
    vector_store = FAISS.from_documents(documents, embeddings)
    vector_store.save_local(VECTOR_STORE_PATH)
    return vector_store

def load_vector_store():
    """
    Loads the FAISS vector store from the local path.
    Uses a global cache to avoid reloading the index on every call.
    """
    global _CACHED_VECTOR_STORE
    
    if _CACHED_VECTOR_STORE is not None:
        return _CACHED_VECTOR_STORE

    if os.path.exists(VECTOR_STORE_PATH):
        print("Loading vector store from disk... (This happens once)")
        embeddings = get_embeddings()
        _CACHED_VECTOR_STORE = FAISS.load_local(VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True)
        return _CACHED_VECTOR_STORE
    else:
        return None
