import os
import logging
from typing import List

# Configure logging
logger = logging.getLogger(__name__)

try:
    from langchain_ollama import ChatOllama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False
    logger.warning("langchain_ollama not found. Running in offline simulation mode.")

def generate_response(query: str, context_chunks: List) -> str:
    """
    Generates a response using the strictly constrained context.
    Tries to use Ollama if available, otherwise falls back to simulation.
    """
    if not context_chunks:
        return "Insufficient validated evidence to answer this query."

    # Construct the prompt context
    context_text = "\n\n".join([c.page_content for c in context_chunks])
    
    # 1. Try Ollama (Local LLM)
    if HAS_OLLAMA:
        try:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            model = os.getenv("OLLAMA_MODEL", "mistral")
            
            # Simple check if "ollama" is reachable is implicitly done by the invoke call, 
            # but we wrap it in try-except to handle connection errors gracefully.
            
            logger.info(f"Attempting to call Ollama at {base_url} with model {model}...")
            
            llm = ChatOllama(
                base_url=base_url,
                model=model,
                temperature=0.1, # Requested: 0.1 (Strict)
                timeout=60.0,    # Increased timeout for 8B model
                num_predict=512, # Requested: 512 tokens
                top_k=40,        # Default/Balanced
                top_p=0.9        # Requested: 0.9
            )

            messages = [
                ("system", "You are a secure ISRO Assistant. Answer using the context. Be extremely concise (2-3 sentences max). If unknown, say 'Insufficient validated evidence'."),
                ("human", f"Context: {context_text}\n\nQuestion: {query}")
            ]
            
            # This might raise an exception if Ollama is not running
            response = llm.invoke(messages)
            return response.content

        except Exception as e:
            logger.warning(f"Ollama connection failed or validation error: {e}. Falling back to offline simulation.")

    # 2. Fallback: Offline Simulation (Simple Extraction)
    logger.info("Using offline fallback (string matching).")
    
    # Simple extraction for demo purposes:
    # If the query asks for "fuel", look for fuel-related sentences in the context
    if "fuel" in query.lower():
        # simple sentence extraction
        for chunk in context_chunks:
            sentences = chunk.page_content.split('.')
            for s in sentences:
                if "fuel" in s.lower() or "propellant" in s.lower():
                    return f"Based on validated documents (Fallback): {s.strip()}."
    
    return f"Based on retrieved context (Fallback):\n{context_chunks[0].page_content[:200]}..."

def generate_response_stream(query: str, context_chunks: List):
    """
    Generates a streaming response using Ollama.
    Falls back to static string if Ollama fails.
    """
    if not context_chunks:
        yield "Insufficient validated evidence to answer this query."
        return

    context_text = "\n\n".join([c.page_content for c in context_chunks])
    
    if HAS_OLLAMA:
        try:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            model = os.getenv("OLLAMA_MODEL", "llama3")
            
            llm = ChatOllama(
                base_url=base_url,
                model=model,
                temperature=0.1,
                timeout=60.0,
                num_predict=512,
                top_k=40,
                top_p=0.9
            )

            messages = [
                ("system", "You are a secure ISRO Assistant. Answer using the context. Be extremely concise. If unknown, say 'Insufficient validated evidence'."),
                ("human", f"Context: {context_text}\n\nQuestion: {query}")
            ]
            
            for chunk in llm.stream(messages):
                yield chunk.content

        except Exception as e:
            logger.warning(f"Ollama stream failed: {e}. Falling back to offline simulation.")
            
            # Fallback Logic (Matching generate_response)
            yield "Based on retrieved context (Fallback): "
            
            # specific heuristic for 'fuel'
            if "fuel" in query.lower():
                found_specific = False
                for chunk in context_chunks:
                    sentences = chunk.page_content.split('.')
                    for s in sentences:
                        if "fuel" in s.lower() or "propellant" in s.lower():
                            yield f"{s.strip()}. "
                            found_specific = True
                            break
                    if found_specific:
                        break
            
            # Default fallback: First chunk snippet
            if context_chunks:
                yield f"\n{context_chunks[0].page_content[:300]}..."
            else:
                 yield "No relevant context found in offline mode."
    else:
        yield "Ollama not installed. Offline mode."


