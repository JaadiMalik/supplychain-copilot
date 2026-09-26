from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.tools.registry import registry


router = APIRouter(tags=["v2 Tool Registry"])


class ToolExecuteRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = {}


@router.get("/tools")
def list_tools():
    return {"count": len(registry.names()), "tools": registry.schemas()}


@router.post("/tools/execute")
def execute_tool(request: ToolExecuteRequest):
    try:
        result = registry.execute(request.name, request.arguments)
        return {"tool": request.name, "result": result}
    except (KeyError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
