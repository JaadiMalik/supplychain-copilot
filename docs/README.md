# SupplyChain Copilot Documentation

SupplyChain Copilot is a **local-first AI decision-support system for supply-chain and procurement workflows**.

It combines:

- structured operational data such as purchase orders, shipments, and inventory;
- supplier contracts and other PDF evidence;
- natural-language SQL over DuckDB;
- RAG over ChromaDB;
- explicit supplier identity resolution;
- a controlled tool-using agent;
- Pydantic-validated LLM outputs;
- deterministic business rules;
- evaluation and observability.

The current reference runtime uses **LM Studio + Qwen 3.5 9B** for generation and **Nomic Embed Text** for embeddings. The business architecture is intentionally separable from the model runtime so that another local model can be evaluated and substituted without redesigning the supply-chain logic.

## Documentation map

| Document | Purpose |
|---|---|
| [System Architecture](architecture/SYSTEM_ARCHITECTURE.md) | System boundaries, module map, end-to-end request flow, RAG, supplier evidence isolation, agent design, and deterministic rules. |
| [Local Model Portability](LOCAL_MODEL_PORTABILITY.md) | How to replace Qwen/LM Studio with another local LLM or runtime safely. |
| [Development Guide](DEVELOPMENT_GUIDE.md) | Environment setup, startup commands, ingestion, tests, common failures, and engineering workflow. |
| [Evaluation and Observability](EVALUATION_AND_OBSERVABILITY.md) | Golden dataset, acceptance gates, retrieval experiments, runtime telemetry, and model-comparison process. |
| [AI Quality v2.1 Notes](AI_QUALITY_V2_1.md) | What was added in the Day 6–10 engineering upgrade and why it matters. |

## Core engineering principle

The LLM is used for probabilistic work:

```text
intent / planning
SQL generation
retrieval assistance
contract-term extraction
natural-language explanation
```

The application remains responsible for deterministic decisions:

```text
supplier identity confirmation
SQL safety validation
evidence attribution
business qualification
final inclusion / exclusion of suppliers and POs
```

> **The model may retrieve, extract, and explain evidence. Deterministic application logic decides whether a supplier or purchase order qualifies.**

Preserve this separation when changing the local model.

## Reference stack

| Layer | Current implementation |
|---|---|
| Frontend | React + Vite |
| API | FastAPI |
| Python | 3.11 |
| Local inference runtime | LM Studio |
| Generation model | `qwen/qwen3.5-9b` |
| Embedding model | `text-embedding-nomic-embed-text-v1.5@q8_0` |
| Vector store | ChromaDB |
| Structured analytics | DuckDB |
| SQL parsing / validation | SQLGlot |
| PDF extraction | PyMuPDF |
| Structured model validation | Pydantic |
| Evaluation | `backend/evals` golden evaluation framework |
| Observability | DuckDB-backed analysis timing and event records |

## Current validation baseline

At the end of the v2.1 AI-quality upgrade, the project passed:

- 10/10 context cases;
- 3/3 agent cases;
- 2/2 RAG cases;
- 15/15 full golden suite;
- supplier-aware RAG isolation test;
- structured-output test;
- hybrid retrieval smoke test;
- failure-mode test;
- observability persistence test;
- FastAPI startup test.

These results are a **baseline for the current model/runtime**, not a guarantee that another local model will behave the same way.

Before replacing the local LLM, read [Local Model Portability](LOCAL_MODEL_PORTABILITY.md) and [Evaluation and Observability](EVALUATION_AND_OBSERVABILITY.md).
