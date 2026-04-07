import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from starlette.requests import Request

from backend.main_engine import rag_system
from backend.session_store import session_store

app = FastAPI(title="Secure ISRO RAG")

templates = Jinja2Templates(directory="app/templates")

class QueryRequest(BaseModel):
    query: str
    role: str
    session_id: str = None

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/login")
async def login_user(req: LoginRequest):
    if req.username == "scientist" and req.password == "isro123":
        return {"success": True, "message": "Authenticated"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/sessions")
async def list_sessions():
    return session_store.get_sessions_list()

@app.post("/sessions/new")
async def create_new_session():
    session_id = session_store.create_session()
    return {"session_id": session_id}

@app.get("/sessions/{session_id}")
async def fetch_session(session_id: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Not found")
    return session

@app.post("/query")
async def process_query(request: QueryRequest):
    user_id = "demo_user" # Hardcoded for demo
    
    # helper generator for StreamingResponse
    async def stream_generator():
        try:
            full_response = ""
            async for chunk in rag_system.process_query_stream(user_id, request.role, request.query):
                full_response += chunk
                yield chunk
                
            if request.session_id:
                session_store.add_message(request.session_id, "user", request.query)
                session_store.add_message(request.session_id, "system", full_response)
                
        except Exception as e:
            yield f"Error: {str(e)}"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
