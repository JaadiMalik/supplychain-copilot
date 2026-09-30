from __future__ import annotations

import json
import re
from typing import TypeVar

import requests
from pydantic import BaseModel, ValidationError

from app.config import LM_STUDIO_URL, LLM_MODEL


T = TypeVar("T", bound=BaseModel)


def call_qwen_text(
    prompt: str,
    max_tokens: int = 700,
) -> str:
    response = requests.post(
        f"{LM_STUDIO_URL}/api/v1/chat",
        json={
            "model": LLM_MODEL,
            "input": prompt,
            "reasoning": "off",
            "temperature": 0.0,
            "max_output_tokens": max_tokens,
            "store": False,
        },
        timeout=120,
    )
    response.raise_for_status()

    output = ""
    for item in response.json().get("output", []):
        if item.get("type") == "message":
            content = item.get("content", "")
            if isinstance(content, str):
                output += content

    return output.strip()


def _extract_json_object(text: str) -> dict:
    cleaned = (
        text
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        raise ValueError("Model output did not contain a JSON object.")

    return json.loads(match.group(0))


def call_qwen_dict(
    prompt: str,
    max_tokens: int = 400,
    retries: int = 1,
) -> dict:
    last_error = None
    current_prompt = prompt

    for attempt in range(retries + 1):
        output = call_qwen_text(
            current_prompt,
            max_tokens=max_tokens,
        )

        try:
            return _extract_json_object(output)
        except (json.JSONDecodeError, ValueError) as error:
            last_error = error

            if attempt >= retries:
                break

            current_prompt = f"""
{prompt}

Your previous response was invalid JSON.

Validation error:
{error}

Return exactly one valid JSON object.
No markdown.
No explanation.
"""

    raise ValueError(
        f"LLM did not return valid JSON after {retries + 1} attempt(s): "
        f"{last_error}"
    )


def call_qwen_structured(
    prompt: str,
    schema: type[T],
    max_tokens: int = 400,
    retries: int = 1,
) -> T:
    last_error = None
    current_prompt = prompt

    for attempt in range(retries + 1):
        data = call_qwen_dict(
            current_prompt,
            max_tokens=max_tokens,
            retries=0,
        )

        try:
            return schema.model_validate(data)
        except ValidationError as error:
            last_error = error

            if attempt >= retries:
                break

            current_prompt = f"""
{prompt}

Your previous JSON did not match the required schema.

Schema:
{json.dumps(schema.model_json_schema(), indent=2)}

Validation error:
{error}

Return corrected JSON only.
"""

    raise ValueError(
        f"LLM output failed schema validation after "
        f"{retries + 1} attempt(s): {last_error}"
    )


def call_qwen_json(
    prompt: str,
    max_tokens: int = 400,
) -> dict:
    # Backward-compatible wrapper used by older code.
    return call_qwen_dict(
        prompt,
        max_tokens=max_tokens,
        retries=1,
    )
