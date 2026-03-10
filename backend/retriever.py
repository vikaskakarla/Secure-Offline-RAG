from backend.vector_store import load_vector_store

def retrieve_context(query, k=1):
    """
    Retrieves the top-k most relevant document chunks for the given query.
    """
    vector_store = load_vector_store()
    if not vector_store:
        return []
    
    # Perform similarity search
    results = vector_store.similarity_search(query, k=k)
    return results
