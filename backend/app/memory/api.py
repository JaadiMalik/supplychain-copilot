from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.memory.service import (
    deactivate_correction,
    get_analysis,
    list_corrections,
    list_history,
    remember_correction,
    remember_supplier_alias,
)


router = APIRouter(tags=["v2 Memory & History"])


class CorrectionRequest(BaseModel):
    correction_type: str
    key: str
    value: str
    note: str = ""


class SupplierAliasMemoryRequest(BaseModel):
    alias_name: str
    canonical_name: str
    note: str = ""


@router.get("/memory/corrections")
def corrections():
    return {"corrections": list_corrections()}


@router.post("/memory/corrections")
def create_correction(request: CorrectionRequest):
    return remember_correction(
        request.correction_type,
        request.key,
        request.value,
        request.note,
    )


@router.post("/memory/supplier-alias")
def create_supplier_alias_memory(request: SupplierAliasMemoryRequest):
    return remember_supplier_alias(
        request.alias_name,
        request.canonical_name,
        request.note,
    )


@router.delete("/memory/corrections/{correction_id}")
def disable_correction(correction_id: str):
    result = deactivate_correction(correction_id)
    if not result["updated"]:
        raise HTTPException(status_code=404, detail="Correction not found.")
    return result


@router.get("/history")
def history(limit: int = 50):
    return {"history": list_history(limit=limit)}


@router.get("/history/{analysis_id}")
def history_item(analysis_id: str):
    item = get_analysis(analysis_id)
    if not item:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return item
