from __future__ import annotations

from pydantic import BaseModel, Field


class CombinedPlan(BaseModel):
    data_question: str
    document_requirement: str


class PenaltyTerms(BaseModel):
    penalty_clause_confirmed: bool = False
    penalty_type: str | None = None
    rate: str | None = None
    calculation_period: str | None = None
    maximum_cap: str | None = None
    exceptions: list[str] = Field(default_factory=list)
