import requests

url = "http://127.0.0.1:1234/api/v1/chat"

payload = {
    "model": "qwen/qwen3.5-9b",
    "input": "Explain a purchase order in one short sentence.",
    "reasoning": "off",
    "max_output_tokens": 100,
    "temperature": 0.2,
    "store": False
}

print("Sending request to Qwen...")

response = requests.post(url, json=payload, timeout=120)
response.raise_for_status()

data = response.json()

for item in data["output"]:
    if item["type"] == "message":
        print("\nQwen:", item["content"])

print("\nDone.")