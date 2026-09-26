from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agent.service import ask_v2


router = APIRouter(tags=["v2 Agent"])


class AgentAskRequest(BaseModel):
    question: str


@router.post("/ask")
def ask_agent(request: AgentAskRequest):
    try:
        return ask_v2(request.question)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
