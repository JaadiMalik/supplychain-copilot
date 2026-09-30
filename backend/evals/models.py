from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvalCase:
    id: str
    question: str
    mode: str
    tags: list[str] = field(default_factory=list)
    expected: dict[str, Any] = field(default_factory=dict)


@dataclass
class CaseResult:
    id: str
    question: str
    mode: str
    passed: bool
    latency_ms: float
    checks: dict[str, Any] = field(default_factory=dict)
    observed: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
