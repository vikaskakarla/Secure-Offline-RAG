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
            _CACHED_EMBEDDINGS = HuggingFaceEmbeddings(
                model_name=local_model_path,
                model_kwargs={'device': 'cpu'}
            )
        else:
            print(f"Local model not found at {local_model_path}, attempting download/load from Hub...")
            _CACHED_EMBEDDINGS = HuggingFaceEmbeddings(
                model_name=MODEL_NAME,
                model_kwargs={'device': 'cpu'}
            )
            
    return _CACHED_EMBEDDINGS

def create_vector_store(documents):
    """
    Creates a FAISS vector store from the provided documents and saves it locally.
    Uses Int8 Scalar Quantization for latency and memory optimization.
    """
    import numpy as np
    from langchain_community.docstore.in_memory import InMemoryDocstore
    
    embeddings = get_embeddings()
    texts = [doc.page_content for doc in documents]
    metadatas = [doc.metadata for doc in documents]
    
    print("Generating embeddings for Int8 FAISS index...")
    text_embeddings = embeddings.embed_documents(texts)
    
    d = len(text_embeddings[0])
    # Create an HNSW index with Int8 Scalar Quantization for maximum speed and memory efficiency
    # HNSW32: Graph-based index with 32 connections per node (lightning-fast O(log N) search)
    # SQ8: 8-bit scalar quantization (small memory footprint)
    index = faiss.index_factory(d, "HNSW32,SQ8")
    
    print("Training HNSW + Int8 Quantizer Index...")
    docs_np = np.array(text_embeddings, dtype=np.float32)
    index.train(docs_np)
    
    # Create the lang-chain vector_store
    vector_store = FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=InMemoryDocstore(),
        index_to_docstore_id={}
    )
    
    # Add embeddings directly
    text_embedding_pairs = list(zip(texts, text_embeddings))
    vector_store.add_embeddings(text_embeddings=text_embedding_pairs, metadatas=metadatas)
    
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
