import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
DATABASE = os.getenv("NEO4J_DATABASE", "neo4j") # Default to neo4j if not set

class GraphStore:
    def __init__(self):
        self.driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

    def close(self):
        self.driver.close()

    def _get_session(self):
        return self.driver.session(database=DATABASE)

    def verify_connectivity(self):
        """
        Verifies if the Neo4j database is reachable.
        """
        try:
            with self._get_session() as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            print(f"Neo4j connectivity check failed: {e}")
            return False

    def setup_schema(self):
        """
        Sets up the initial schema constraints for the Knowledge Graph.
        """
        with self._get_session() as session:
            # Create constraints to ensure uniqueness using correct Neo4j 5.x syntax
            # Syntax: CREATE CONSTRAINT [name] IF NOT EXISTS FOR (n:Label) REQUIRE n.prop IS UNIQUE
            
            try:
                session.run("CREATE CONSTRAINT mission_name IF NOT EXISTS FOR (m:Mission) REQUIRE m.name IS UNIQUE")
                session.run("CREATE CONSTRAINT lv_name IF NOT EXISTS FOR (lv:LaunchVehicle) REQUIRE lv.name IS UNIQUE")
                session.run("CREATE CONSTRAINT stage_name IF NOT EXISTS FOR (s:Stage) REQUIRE s.name IS UNIQUE")
                session.run("CREATE CONSTRAINT engine_name IF NOT EXISTS FOR (e:Engine) REQUIRE e.name IS UNIQUE")
            except Exception as e:
                print(f"Schema setup warning (might be older Neo4j version): {e}")

    def add_entity(self, label, properties):
        """
        Adds a node to the graph with the given label and properties.
        """
        query = f"MERGE (n:{label} {{name: $name}}) SET n += $props"
        with self._get_session() as session:
            session.run(query, name=properties.get("name"), props=properties)

    def add_relationship(self, start_label, start_name, end_label, end_name, relationship_type):
        """
        Adds a relationship between two nodes.
        """
        query = f"""
        MATCH (a:{start_label} {{name: $start_name}})
        MATCH (b:{end_label} {{name: $end_name}})
        MERGE (a)-[:{relationship_type}]->(b)
        """
        with self._get_session() as session:
            session.run(query, start_name=start_name, end_name=end_name)
    
    def query_facts(self, entity_name):
        """
        Retrieves all facts related to a specific entity.
        """
        query = """
        MATCH (n {name: $name})-[r]-(m)
        RETURN type(r) as relationship, labels(m) as target_label, m.name as target_name
        """
        with self._get_session() as session:
            result = session.run(query, name=entity_name)
            return [record.data() for record in result]

if __name__ == "__main__":
    # Test connection
    try:
        graph = GraphStore()
        graph.setup_schema()
        print("Connected to Neo4j and schema setup complete.")
        graph.close()
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")
