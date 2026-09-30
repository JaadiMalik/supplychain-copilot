# Local Model Portability Guide

## 1. Goal

The current reference implementation uses:

```text
LM Studio
  generation: qwen/qwen3.5-9b
  embeddings: text-embedding-nomic-embed-text-v1.5@q8_0
```

The goal is to evaluate and adopt another local model without changing the supply-chain architecture.

A model/runtime replacement should be treated as an **adapter change + evaluation exercise**, not a rewrite of business logic.

## 2. Current provider-specific touchpoints

The most important model/runtime-specific files are:

```text
backend/app/config.py
backend/app/agent/llm.py
backend/app/analytics/sql_generator.py
backend/app/rag/embeddings.py
backend/app/health/service.py
```

### Current configuration

The current repository defines LM Studio URL and model IDs as Python constants.

Reference values:

```text
LM_STUDIO_URL=http://127.0.0.1:1234
LLM_MODEL=qwen/qwen3.5-9b
EMBED_MODEL=text-embedding-nomic-embed-text-v1.5@q8_0
```

Important: the current `config.py` uses constants directly. Do not assume an `.env` file overrides these values unless environment loading has been implemented.

A future portability refactor should move toward separate generation and embedding settings, for example:

```text
LOCAL_AI_PROVIDER=lmstudio
LOCAL_AI_BASE_URL=http://127.0.0.1:1234
LOCAL_AI_MODEL=qwen/qwen3.5-9b
LOCAL_EMBED_PROVIDER=lmstudio
LOCAL_EMBED_BASE_URL=http://127.0.0.1:1234
LOCAL_EMBED_MODEL=text-embedding-nomic-embed-text-v1.5@q8_0
RAG_RETRIEVAL_MODE=hybrid
```

Generation and embeddings should remain separately configurable because they may be served by different local runtimes.

## 3. Stable application contract

The rest of the project should depend on a small provider-neutral interface.

### Text generation

```python
def generate_text(prompt: str, max_tokens: int = 700) -> str:
    ...
```

Requirements:

- return plain text;
- support deterministic/low-temperature generation;
- expose a reasonable timeout;
- raise a clear error for runtime failures.

### Structured generation

```python
def generate_structured(
    prompt: str,
    schema: type[BaseModel],
    max_tokens: int = 400,
    retries: int = 1,
) -> BaseModel:
    ...
```

Requirements:

- ask the model for JSON;
- parse JSON defensively;
- validate with Pydantic;
- retry once with validation feedback;
- fail explicitly if output remains invalid.

Keep Pydantic validation even if the local runtime claims to support native schema/JSON output.

### Embeddings

```python
def embed_document(text: str) -> list[float]:
    ...

def embed_query(text: str) -> list[float]:
    ...
```

Requirements:

- return numeric vectors;
- use compatible document/query embeddings;
- preserve task prefixes only when required by the embedding model;
- re-index all document chunks when changing embedding models.

## 4. Current LM Studio behavior

Current generation uses LM Studio's native:

```text
POST /api/v1/chat
```

with low-temperature generation and:

```json
{"reasoning": "off"}
```

The embedding path uses LM Studio's OpenAI-compatible `/v1/embeddings` endpoint through the OpenAI Python client.

Do not assume another local runtime uses the same endpoint combination or response shape.

## 5. Runtime adapter patterns

The following are implementation patterns. Verify the current API of the selected runtime before adopting them.

### OpenAI-compatible local server

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:PORT/v1",
    api_key="local",
)

def generate_text(prompt: str, max_tokens: int = 700) -> str:
    response = client.chat.completions.create(
        model="LOCAL_MODEL_ID",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""
```

The existing JSON extraction and Pydantic validation can stay above this adapter.

### Ollama native API pattern

```python
import requests

def generate_text(prompt: str, max_tokens: int = 700) -> str:
    response = requests.post(
        "http://127.0.0.1:11434/api/chat",
        json={
            "model": "MODEL_NAME",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]
```

Exact options can differ across Ollama/model versions. Normalize provider output into the application's stable `str` contract.

### llama.cpp / vLLM / LocalAI-style servers

When the server exposes an OpenAI-compatible API, use the OpenAI-compatible adapter pattern and verify:

- model ID;
- chat endpoint;
- embedding endpoint;
- JSON behavior;
- context length;
- timeout behavior.

## 6. Do not force one model to do everything

A good local deployment may use:

```text
generation model: one model
embedding model: another model
```

This is already how the reference system works.

A candidate chat model should be judged on:

- instruction following;
- JSON reliability;
- SQL generation;
- evidence extraction;
- tool-selection consistency;
- latency;
- memory use.

A candidate embedding model should be judged on:

- retrieval hit rate;
- exact commercial-term retrieval;
- supplier-filtered retrieval;
- indexing latency;
- query latency.

## 7. Model swap procedure

### Step 1 — Capture the current baseline

From `backend`:

```bash
PYTHONPATH=. python -m evals.runner
PYTHONPATH=. python -m evals.runner --mode rag
PYTHONPATH=. python -m evals.runner --mode agent
PYTHONPATH=. python -m evals.experiments.retrieval_compare
```

Record pass rates and latency.

### Step 2 — Change generation only

Keep the existing Nomic embedding model and Chroma index.

Change only the generation adapter/model first. This isolates generation quality from retrieval changes.

Run:

```bash
PYTHONPATH=. python scripts/test_day8_structured_outputs.py
PYTHONPATH=. python scripts/test_day10_failure_modes.py
PYTHONPATH=. python -m evals.runner --mode agent
PYTHONPATH=. python -m evals.runner
```

### Step 3 — Classify failures

Check whether failure is in:

- context/planning;
- tool selection;
- JSON/schema output;
- SQL generation;
- evidence extraction;
- synthesis.

Do not modify prompts until the failing layer is known.

### Step 4 — Change embeddings separately

If testing a new embedding model:

1. configure its adapter;
2. verify task-prefix requirements;
3. clear/rebuild document vectors;
4. re-index PDFs;
5. run retrieval comparison;
6. run RAG tests;
7. run the full suite.

Never compare retrieval quality using document vectors created by another embedding model.

## 8. Minimum acceptance gate for another local LLM

Recommended minimum gate:

```text
structured-output test            PASS
supplier-aware RAG test           PASS
failure-mode test                 PASS
RAG golden cases                  2/2
agent golden cases                3/3
full golden suite                 15/15
FastAPI startup                   PASS
observability persistence         PASS
```

If a new model fails some tests but provides a meaningful advantage, document the tradeoff explicitly instead of silently lowering the gate.

## 9. Model characteristics that matter

### Instruction following

The model must follow constraints such as:

```text
Return JSON only.
Use one tool.
Do not invent columns.
Do not infer missing contract terms.
```

### Structured-output reliability

A capable model that frequently emits invalid JSON increases retries and latency.

### SQL competence

The model must:

- use available tables only;
- use available columns only;
- produce DuckDB-compatible SQL;
- preserve read-only behavior;
- use explicit status fields appropriately.

### Extraction discipline

The model must distinguish evidence from inference. Unsupported contract inference is a failure.

### Latency

Use observability to compare:

```text
planner_duration_ms
tool_duration_ms
synthesis_duration_ms
total_duration_ms
```

### Context window

A very large context window is not automatically better. The system is retrieval-oriented; prioritize retrieval quality, structured-output reliability, and instruction adherence.

## 10. Embedding-model migration

Changing only the chat model:

```text
No Chroma re-index required.
```

Changing the embedding model:

```text
Re-index required.
```

Safe migration:

```text
stop API
 -> configure embedding model
 -> rebuild Chroma collection
 -> re-index documents
 -> run retrieval tests
 -> run RAG tests
 -> run full eval
```

## 11. Prompt portability

Prompts should describe the task, not the provider.

Good:

```text
Return exactly one JSON object matching this schema.
```

When changing models:

1. run existing prompts first;
2. identify real failures;
3. modify only the prompts that need changes;
4. rerun the full suite.

This prevents overfitting the application to one model.

## 12. Recommended future provider abstraction

A clean next refactor is:

```text
app/ai/
├── base.py
├── factory.py
├── lmstudio.py
├── openai_compatible.py
├── ollama.py
└── embeddings.py
```

Possible interfaces:

```python
class LocalLLM:
    def text(self, prompt: str, max_tokens: int) -> str:
        ...

    def structured(self, prompt, schema, max_tokens, retries):
        ...

class EmbeddingProvider:
    def document(self, text: str) -> list[float]:
        ...

    def query(self, text: str) -> list[float]:
        ...
```

This is a recommended future refactor, not the current repository structure.

## 13. Comparison template

| Metric | Reference Qwen | Candidate |
|---|---:|---:|
| Full eval | 15/15 | |
| Agent eval | 3/3 | |
| RAG eval | 2/2 | |
| Structured JSON | PASS | |
| Supplier isolation | PASS | |
| Agent latency | baseline | |
| Memory use | local measurement | |
| Notes | | |

The best local model for this project is the model that preserves required business reliability at an acceptable latency and memory footprint.
