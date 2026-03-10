from backend.graph_store import GraphStore
import re

class Validator:
    def __init__(self):
        self.graph_store = None
        try:
            temp_store = GraphStore()
            if temp_store.verify_connectivity():
                self.graph_store = temp_store
            else:
                print("Warning: Graph Store connectivity failed. Validation disabled.")
        except Exception as e:
            print(f"Warning: Graph Store unavailable ({e}). Validation disabled.")

    def validate_answer(self, query, vector_context):
        """
        Validates the retrieved vector context against the Knowledge Graph facts.
        Returns a validation score and reason.
        """
        if not self.graph_store:
            return True, "Graph Validation Skipped (Offline)"

        # 1. Extract Entity from Query (Heuristic)
        entities = self._extract_entities(query)
        if not entities:
            return True, "No entities found for validation."

        start_entity = entities[0]
        
        # 2. Query Knowledge Graph for Facts regarding this entity
        graph_facts = self.graph_store.query_facts(start_entity)
        if not graph_facts:
            return False, f"Entity '{start_entity}' not found in Knowledge Graph."

        # 3. Check Consistency
        # For simplicity: Check if any fact in graph contradicts vector context
        # (This is a simplified check. Real implementation requires NLI model)
        
        # Heuristic Check: If query asks about 'Stage' and retrieved context mentions differ from graph
        # Example: Query "PSLV Stage 5", Graph "PSLV has 4 stages" -> Mismatch
        
        max_stage_in_graph = 0
        if "Stage" in query:
             # Find max stage number in graph facts
             for fact in graph_facts:
                 if fact['target_label'] == ['Stage']:
                     # Extract number from Stage name e.g. "Stage 3" -> 3
                     num = re.findall(r'\d+', fact['target_name'])
                     if num:
                         max_stage_in_graph = max(max_stage_in_graph, int(num[0]))

             if max_stage_in_graph > 0:
                 # Check if query asks for a higher stage
                 query_stage_nums = re.findall(r'Stage\s*(\d+)', query, re.IGNORECASE)
                 if query_stage_nums:
                     asked_stage = int(query_stage_nums[0])
                     if asked_stage > max_stage_in_graph:
                         return False, f"Graph Fact Conflict: {start_entity} only has {max_stage_in_graph} stages. Found request for Stage {asked_stage}."

        return True, "Validation Passed"

    def _extract_entities(self, text):
        # reuse logic or simplified extraction
        # For demo, just check for PSLV, GSLV
        matches = re.findall(r"\b(PSLV|GSLV|LVM3)\b", text)
        return matches
