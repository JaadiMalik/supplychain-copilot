from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.context.resolver import resolve_context


router = APIRouter(tags=["v2 Context Resolver"])


class ContextResolveRequest(BaseModel):
    question: str


@router.post("/context/resolve")
def resolve_context_api(request: ContextResolveRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        return resolve_context(question)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
