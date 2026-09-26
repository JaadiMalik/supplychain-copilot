import json
import requests

from app.config import LM_STUDIO_URL, LLM_MODEL


def call_qwen_text(prompt: str, max_tokens: int = 700) -> str:
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
    data = response.json()
    output = ""
    for item in data.get("output", []):
        if item.get("type") == "message":
            content = item.get("content", "")
            if isinstance(content, str):
                output += content
    return output.strip()


def call_qwen_json(prompt: str, max_tokens: int = 400) -> dict:
    output = call_qwen_text(prompt, max_tokens=max_tokens)
    output = output.replace("```json", "").replace("```", "").strip()
    return json.loads(output)
