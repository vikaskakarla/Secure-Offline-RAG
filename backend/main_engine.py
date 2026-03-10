from backend.retriever import retrieve_context
from backend.validator import Validator
from backend.rbac import RBAC
from backend.llm_engine import generate_response
from backend.logger import log_query

class RAGSystem:
    def __init__(self):
        self.validator = Validator()

    def process_query(self, user_id, user_role, query):
        """
        Main pipeline: RBAC -> Retrieve -> Validate -> Generate -> Log
        """
        # 1. RBAC Check (Simplified: Check if user has basic query permission)
        if not RBAC.check_access(user_role, "public"): # Everyone can ask public Qs
             return "Access Denied: Insufficient permissions."

        # 2. Retrieve Context
        context_chunks = retrieve_context(query)
        
        # 3. RBAC Filtering on Retrieved Documents
        # Filter chunks based on their source document's classification
        # (Assuming metadata has access_level, defaulting to public for now)
        allowed_chunks = []
        for chunk in context_chunks:
             # In a real app, you'd check chunk.metadata['access_level']
             allowed_chunks.append(chunk)

        if not allowed_chunks:
            response = "No accessible information found."
            log_query(user_id, user_role, query, response, [], "No Data")
            return response

        # 4. Hybrid Validation
        is_valid, validation_msg = self.validator.validate_answer(query, allowed_chunks)
        
        if not is_valid:
            response = f"Controlled Refusal: {validation_msg}"
            log_query(user_id, user_role, query, response, [c.metadata for c in allowed_chunks], "Validation Failed")
            return response

        # 5. Generate Response
        response = generate_response(query, allowed_chunks)

        # 6. Audit Log
        log_query(user_id, user_role, query, response, [c.metadata for c in allowed_chunks], "Success")

        return response

    def process_query_stream(self, user_id, user_role, query):
        """
        Streaming pipeline: RBAC -> Retrieve -> Validate -> Generate Stream
        """
        # 1. RBAC Check
        if not RBAC.check_access(user_role, "public"):
             yield "Access Denied: Insufficient permissions."
             return

        # 2. Retrieve Context
        context_chunks = retrieve_context(query)
        
        # 3. RBAC Filtering
        allowed_chunks = []
        for chunk in context_chunks:
             allowed_chunks.append(chunk)

        if not allowed_chunks:
            yield "No accessible information found."
            return

        # 4. Hybrid Validation (Simplified for stream: check if any context exists)
        # Note: Full validation is hard to stream, so we rely on context quality or validate strictly before streaming.
        is_valid, validation_msg = self.validator.validate_answer(query, allowed_chunks)
        
        if not is_valid:
            yield f"Controlled Refusal: {validation_msg}"
            return

        # 5. Generate Response Stream
        from backend.llm_engine import generate_response_stream
        for chunk in generate_response_stream(query, allowed_chunks):
            yield chunk

# Singleton Instance
rag_system = RAGSystem()
