from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import models
import schemas
import auth
from database import get_db
import rag_service

router = APIRouter(prefix="/api/rag", tags=["RAG AI Memory & Assistant"])

@router.post("/query", response_model=schemas.RAGQueryResponse)
def query_rag_assistant(
    req: schemas.RAGQueryRequest,
    current_user: models.User = Depends(auth.get_current_user)
):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    result = rag_service.run_rag_pipeline(
        user_id=current_user.id,
        user_name=current_user.name,
        question=req.question,
        provider=req.provider or "ollama",
        model_name=req.model_name
    )

    return schemas.RAGQueryResponse(**result)

@router.get("/memories", response_model=List[Dict[str, Any]])
def get_user_rag_memories(
    current_user: models.User = Depends(auth.get_current_user)
):
    # Fetch recent memories for inspection
    memories = rag_service.RetrievalAgent.retrieve(current_user.id, "task productivity activity completed created delayed", top_k=20)
    return memories
