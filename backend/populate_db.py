from backend.ingestion import load_documents, split_documents
from backend.vector_store import create_vector_store
from backend.graph_store import GraphStore
import re

# Simple heuristic entity extraction for demonstration (Offline/Rule-based)
def extract_entities(text):
    """
    Extracts basic entities like Missions, Launch Vehicles, Stages, Engines based on patterns.
    This is a simplistic rule-based extractor for the offline demo.
    """
    entities = {
        "Mission": set(),
        "LaunchVehicle": set(),
        "Stage": set(),
        "Engine": set()
    }
    
    # Example patterns (You would expand these based on your specific ISRO docs)
    # detecting PSLV, GSLV variants
    lv_matches = re.findall(r"\b(PSLV|GSLV|LVM3|SSLV)[-A-Za-z0-9]*\b", text)
    entities["LaunchVehicle"].update(lv_matches)
    
    # detecting Stages
    stage_matches = re.findall(r"\b(Stage\s*\d+|First\s*Stage|Second\s*Stage|Third\s*Stage)\b", text, re.IGNORECASE)
    entities["Stage"].update(stage_matches)
    
    # detecting Engines
    engine_matches = re.findall(r"\b(Vikas|Cryogenic|CE-20|CE-7.5|S200)\b", text, re.IGNORECASE)
    entities["Engine"].update(engine_matches)
    
    # detecting Missions
    mission_matches = re.findall(r"\b(Chandrayaan-\d+|Mangalyaan|Aditya-L1|Gaganyaan)\b", text)
    entities["Mission"].update(mission_matches)

    return entities

def populate_database(folder_path="data/isro_docs"):
    print(f"Loading documents from {folder_path}...")
    docs = load_documents(folder_path)
    if not docs:
        print("No documents found to process.")
        return

    print(f"Loaded {len(docs)} documents.")
    
    # 1. Populate Vector Store
    print("Splitting documents...")
    chunks = split_documents(docs)
    print(f"Created {len(chunks)} chunks.")
    
    print("Creating Vector Store (FAISS)...")
    create_vector_store(chunks)
    print("Vector Store created and saved.")

    # 2. Populate Knowledge Graph
    print("Connecting to Knowledge Graph (Neo4j)...")
    try:
        graph = GraphStore()
        graph.setup_schema()
        
        print("Extracting entities and populating Graph...")
        for doc in docs:
            text = doc.page_content
            extracted = extract_entities(text)
            
            # Add Launch Vehicles
            for lv in extracted["LaunchVehicle"]:
                graph.add_entity("LaunchVehicle", {"name": lv})
            
            # Add Stages
            for stage in extracted["Stage"]:
                graph.add_entity("Stage", {"name": stage})

            # Add Engines
            for engine in extracted["Engine"]:
                graph.add_entity("Engine", {"name": engine})

            # Add Missions
            for mission in extracted["Mission"]:
                graph.add_entity("Mission", {"name": mission})
            
            # Create Relationships (Heuristic: if they appear in same doc, link them)
            # Link LV to Stage
            for lv in extracted["LaunchVehicle"]:
                for stage in extracted["Stage"]:
                    graph.add_relationship("LaunchVehicle", lv, "Stage", stage, "HAS_STAGE")
            
            # Link Stage to Engine
            for stage in extracted["Stage"]:
                for engine in extracted["Engine"]:
                    graph.add_relationship("Stage", stage, "Engine", engine, "USES_ENGINE")

        graph.close()
        print("Knowledge Graph populated successfully.")
    except Exception as e:
        print(f"Skipping Graph Population due to error (is Neo4j running?): {e}")

if __name__ == "__main__":
    populate_database()
