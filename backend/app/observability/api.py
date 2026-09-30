from fastapi import APIRouter

from app.observability.service import get_observability_summary


router = APIRouter(tags=["v2 Observability"])


@router.get("/observability/summary")
def observability_summary(limit: int = 100):
    return get_observability_summary(limit=limit)
