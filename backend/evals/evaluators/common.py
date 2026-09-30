from __future__ import annotations

from typing import Any


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).casefold().split())


def contains_all(text: str, needles: list[str]) -> tuple[bool, list[str]]:
    haystack = normalize_text(text)
    missing = [item for item in needles if normalize_text(item) not in haystack]
    return not missing, missing


def contains_none(text: str, needles: list[str]) -> tuple[bool, list[str]]:
    haystack = normalize_text(text)
    found = [item for item in needles if normalize_text(item) in haystack]
    return not found, found


def recursive_find_values(value: Any, key: str) -> list[Any]:
    found = []

    if isinstance(value, dict):
        for current_key, current_value in value.items():
            if current_key == key:
                found.append(current_value)
            found.extend(recursive_find_values(current_value, key))

    elif isinstance(value, list):
        for item in value:
            found.extend(recursive_find_values(item, key))

    return found


def recursive_collect_sources(value: Any) -> list[dict]:
    sources = []

    if isinstance(value, dict):
        if "document" in value and "page" in value:
            sources.append(
                {
                    "document": value.get("document"),
                    "page": value.get("page"),
                }
            )
        for child in value.values():
            sources.extend(recursive_collect_sources(child))

    elif isinstance(value, list):
        for child in value:
            sources.extend(recursive_collect_sources(child))

    unique = []
    seen = set()

    for source in sources:
        key = (source.get("document"), source.get("page"))
        if key not in seen:
            seen.add(key)
            unique.append(source)

    return unique
