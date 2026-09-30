from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class PlannerDecision(BaseModel):
    action: str
    tool_name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""

    @field_validator("action")
    @classmethod
    def normalize_action(cls, value: str) -> str:
        return value.strip().casefold()


class SourceSelection(BaseModel):
    source_numbers: list[int] = Field(default_factory=list)
