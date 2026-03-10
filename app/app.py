import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from starlette.requests import Request

from backend.main_engine import rag_system

app = FastAPI(title="Secure ISRO RAG")

templates = Jinja2Templates(directory="app/templates")

class QueryRequest(BaseModel):
    query: str
    role: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/query")
async def process_query(request: QueryRequest):
    user_id = "demo_user" # Hardcoded for demo
    
    # helper generator for StreamingResponse
    async def stream_generator():
        try:
            for chunk in rag_system.process_query_stream(user_id, request.role, request.query):
                yield chunk
        except Exception as e:
            yield f"Error: {str(e)}"

    return StreamingResponse(stream_generator(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
