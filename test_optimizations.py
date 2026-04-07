from backend.vector_store import create_vector_store, load_vector_store
from langchain_core.documents import Document
from backend.main_engine import rag_system
import time

print("Testing Vector DB Creation...")
docs = [
    Document(page_content="ISRO is the Indian Space Research Organisation.", metadata={"source": "test"}),
    Document(page_content="PSLV is a launch vehicle developed by ISRO.", metadata={"source": "test"}),
]
vs = create_vector_store(docs)
print("Vector Store Created successfully with Int8 Quantization.")

print("Testing Query Caching...")
t0 = time.time()
r1 = rag_system.process_query("test_user", "public", "what is ISRO?")
t1 = time.time()
print(f"First query took: {t1 - t0:.2f}s")
print(f"Response: {r1}")

t2 = time.time()
r2 = rag_system.process_query("test_user", "public", "what is ISRO?") 
t3 = time.time()
print(f"Second (cached) query took: {t3 - t2:.2f}s")
print(f"Response: {r2}")
