import os
from dotenv import load_dotenv
load_dotenv() 

from fastapi import FastAPI, Depends, HTTPException, status, Header
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from orchestrator.engine import QueryOrchestrator
from history.engine import HistoryEngine
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from contextlib import asynccontextmanager
import uuid
import uvicorn

# Global orchestrator and history instances
orchestrator: QueryOrchestrator = None
history_engine: HistoryEngine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator, history_engine
    logger.info("Initializing Assistant Components...")
    orchestrator = QueryOrchestrator()
    history_engine = HistoryEngine()
    yield
    logger.info("Shutting down...")

app = FastAPI(title="Data AI Assistant (SaaS Mode)", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    prompt: str
    conversation_id: Optional[str] = None

class QueryResult(BaseModel):
    intent: Optional[str] = None
    content: Optional[str] = None
    sql: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None
    insights: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    conversation_id: Optional[str] = None

def get_token(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format.")
    return authorization.split(" ")[1]

@app.post("/query", response_model=QueryResult)
async def process_query(
    request: QueryRequest,
    jwt_token: str = Depends(get_token)
):
    logger.info("API: Processing request.")
    
    try:
        # 1. Run Pipeline
        result = await orchestrator.execute_pipeline(request.prompt, jwt_token)
        
        # 2. Extract Identity for History
        identity = orchestrator.auth.verify_auth_identity(jwt_token)
        user_id = identity.get("user_id") if identity else None
        
        # 3. Handle Conversation Persistence
        conv_id = request.conversation_id
        if user_id:
            if not conv_id:
                # Auto-create conversation if first message
                conv_id = history_engine.create_conversation(user_id, title=request.prompt[:40])
            
            # Save User Message
            history_engine.save_message(conv_id, "user", request.prompt)
            # Save Assistant Response
            if not result.get("error"):
                history_engine.save_message(conv_id, "assistant", result.get("content", ""), data=result)

        # 4. Error Handling
        if result.get("error"):
            status_code = 401 if "Unauthorized" in result["error"] else 400
            raise HTTPException(status_code=status_code, detail=result["error"])
            
        return {**result, "conversation_id": conv_id}

    except HTTPException as e: raise e
    except Exception as e:
        logger.error(f"API ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- HISTORY ENDPOINTS ---

@app.get("/history/conversations")
async def list_conversations(jwt_token: str = Depends(get_token)):
    identity = orchestrator.auth.verify_auth_identity(jwt_token)
    if not identity: raise HTTPException(status_code=401)
    return history_engine.get_conversations(identity["user_id"])

@app.get("/history/conversations/{conversation_id}/messages")
async def load_messages(conversation_id: str, jwt_token: str = Depends(get_token)):
    identity = orchestrator.auth.verify_auth_identity(jwt_token)
    if not identity: raise HTTPException(status_code=401)
    # Security: Ensure user owns conversation (skipped for dev brevity, but enforced by RLS in Engine)
    return history_engine.get_messages(conversation_id)

@app.delete("/history/conversations/{conversation_id}")
async def delete_item(conversation_id: str, jwt_token: str = Depends(get_token)):
    identity = orchestrator.auth.verify_auth_identity(jwt_token)
    if not identity: raise HTTPException(status_code=401)
    history_engine.delete_conversation(conversation_id)
    return {"status": "deleted"}

class UpdateConversationRequest(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None

@app.patch("/history/conversations/{conversation_id}")
async def update_item(conversation_id: str, request: UpdateConversationRequest, jwt_token: str = Depends(get_token)):
    identity = orchestrator.auth.verify_auth_identity(jwt_token)
    if not identity: raise HTTPException(status_code=401)
    updates = request.dict(exclude_unset=True)
    history_engine.update_conversation(conversation_id, updates)
    return {"status": "updated"}

from fastapi.responses import StreamingResponse

@app.post("/query/stream")
async def stream_query(
    request: QueryRequest,
    jwt_token: str = Depends(get_token)
):
    logger.info("API: Processing streaming request.")
    
    # 1. AUTH
    identity = orchestrator.auth.verify_auth_identity(jwt_token)
    user_id = identity.get("user_id") if identity else None
    if not user_id: raise HTTPException(status_code=401)

    # 2. CONVERSATION ID (If first message)
    conv_id = request.conversation_id
    if not conv_id:
        conv_id = history_engine.create_conversation(user_id, title=request.prompt[:40])
        if not conv_id:
            logger.error("API: Failed to establish persistent conversation context. Check DB logs.")
            # Fallback to a temporary ID so the AI can still answer even if history fails
            conv_id = f"tmp-{uuid.uuid4()}" 
    
    # Save User Msg (Immediate Sync)
    if not conv_id.startswith("tmp-"):
        history_engine.save_message(conv_id, "user", request.prompt)

    async def event_generator():
        full_content = ""
        # 3. YIELD CONV_ID IMMEDIATELY for Instant UI Feedback
        yield f" __CONV_ID__:{conv_id}"
        
        # 4. STREAM FROM ENGINE
        async for token in orchestrator.stream_pipeline(request.prompt, jwt_token):
            full_content += token
            yield token
        
        # 5. Persistence at END of stream
        if conv_id and not conv_id.startswith("tmp-"):
            history_engine.save_message(conv_id, "assistant", full_content, data={"conversation_id": conv_id})

    return StreamingResponse(event_generator(), media_type="text/plain")

@app.get("/health")
def health_check():
    return {"status": "ok (History + SSL Ready)"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
