from fastapi import APIRouter

from app.agent.api import router as agent_router
from app.context.api import router as context_router
from app.memory.api import router as memory_router
from app.reports.api import router as reports_router
from app.tools.api import router as tools_router


router = APIRouter(prefix="/v2")
router.include_router(context_router)
router.include_router(tools_router)
router.include_router(agent_router)
router.include_router(memory_router)
router.include_router(reports_router)
