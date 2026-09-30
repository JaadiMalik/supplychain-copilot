from __future__ import annotations

import json
from pathlib import Path

from evals.models import EvalCase


EVALS_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = EVALS_DIR / "datasets" / "supplychain_golden.json"


def load_cases(path: str | Path | None = None) -> list[EvalCase]:
    dataset_path = Path(path) if path else DEFAULT_DATASET
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))

    return [
        EvalCase(
            id=item["id"],
            question=item["question"],
            mode=item.get("mode", "context"),
            tags=item.get("tags", []),
            expected=item.get("expected", {}),
        )
        for item in payload.get("cases", [])
    ]
