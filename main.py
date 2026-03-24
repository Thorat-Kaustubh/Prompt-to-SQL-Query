from fastapi import FastAPI, Depends, HTTPException, status, Header
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from orchestrator.engine import QueryOrchestrator
import uvicorn
import os
from dotenv import load_dotenv
from loguru import logger

# 1. Environment & Database Initialization (Security Architect Standards)
load_dotenv()

app = FastAPI(title="Text-to-SQL AI System (Supabase Enforced)")

# 2. Dependency Injection (Stateless Frontend Layer)
orchestrator = QueryOrchestrator()

class QueryRequest(BaseModel):
    prompt: str

class QueryResult(BaseModel):
    sql: str
    results: List[Dict[str, Any]]
    meta: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.post("/query", response_model=QueryResult)
async def process_query(
    request: QueryRequest,
    authorization: str = Header(..., description="Supabase JWT token (Bearer <token>)")
):
    """
    Identity-Aware Text-to-SQL Endpoint (Security Standard).
    - Authorization is verified using Supabase Auth.
    - Identity (auth.uid) is passed downstream to enforce RLS in Postgres.
    """
    logger.info("API: Processing secure Text-to-SQL request.")
    
    # Extract Bearer token
    if not authorization.startswith("Bearer "):
         raise HTTPException(status_code=401, detail="Invalid token format. Expected 'Bearer <token>'")
    
    jwt_token = authorization.split(" ")[1]
    
    try:
        # Run orchestrated pipeline (Security context included)
        result = await orchestrator.execute_pipeline(request.prompt, jwt_token)
        
        # Check for error in the pipeline response (Identity failure / RLS block)
        if result.get("error"):
            # Identify if it's an Auth failure (401) or a Validation failure (400)
            status_code = 401 if "Unauthorized" in result["error"] else 400
            raise HTTPException(status_code=status_code, detail=result["error"])
            
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"API ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/health")
def health_check():
    return {"status": "ok (Supabase Enforced)"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
