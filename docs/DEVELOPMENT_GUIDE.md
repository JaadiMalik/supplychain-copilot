# Development Guide

## 1. Reference development environment

The project has been validated locally on Apple Silicon using:

```text
Python 3.11
Conda environment: supplychain-copilot
LM Studio local server
Qwen 3.5 9B
Nomic Embed Text
FastAPI
React + Vite
DuckDB
ChromaDB
```

A reference development machine used during the project had 18 GB unified memory. On memory-constrained systems, keep only the required generation model and embedding model loaded.

## 2. Clone

```bash
git clone https://github.com/JaadiMalik/supplychain-copilot.git
cd supplychain-copilot
```

## 3. Python environment

```bash
conda create -n supplychain-copilot python=3.11
conda activate supplychain-copilot
```

Verify:

```bash
which python
python --version
```

Expected pattern:

```text
.../envs/supplychain-copilot/bin/python
Python 3.11.x
```

Install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Important dependencies include FastAPI, Uvicorn, Requests, the OpenAI Python client, PyMuPDF, ChromaDB, DuckDB, Pandas, NumPy, OpenPyXL, SQLGlot, python-docx, and ReportLab.

## 4. Start the local AI runtime

Reference LM Studio configuration:

```text
Server: http://127.0.0.1:1234
Generation: qwen/qwen3.5-9b
Embeddings: text-embedding-nomic-embed-text-v1.5@q8_0
```

The current generation code uses LM Studio's native chat endpoint and disables reasoning output for the reference Qwen model. Embeddings use the OpenAI-compatible embeddings endpoint.

## 5. Start FastAPI

Start from the backend directory:

```bash
cd /path/to/supplychain-copilot/backend
conda activate supplychain-copilot
python -m uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

A `404` on `GET /` is harmless because a root route is not required.

## 6. Start the frontend

In a second terminal:

```bash
cd /path/to/supplychain-copilot/frontend
npm install
npm run dev
```

Reference URL:

```text
http://localhost:5173
```

## 7. Health checks

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/v2/observability/summary
curl -I http://127.0.0.1:8000/docs
```

## 8. Structured-data ingestion

The pipeline is:

```text
CSV/XLSX
 -> Pandas/OpenPyXL
 -> normalized tables
 -> DuckDB
 -> schema discovery
 -> natural-language SQL
```

When testing natural-language SQL, inspect both the generated SQL and final rows. Do not judge correctness only from the natural-language answer.

## 9. PDF ingestion

```text
PDF
 -> page extraction
 -> chunking
 -> metadata
 -> embedding
 -> ChromaDB
```

If a PDF is re-uploaded under the same filename, old chunks are removed before re-indexing.

Re-index after changes to metadata extraction, chunking, embedding model, or embedding preprocessing.

Day 7 helper:

```bash
cd backend
PYTHONPATH=. python scripts/reindex_documents_day7.py
```

## 10. Supplier alias registry

Supplier legal identity is explicit.

```text
Atlas Industrial
 -> Atlas Industrial Supplies Ltd.
```

Do not replace this with automatic fuzzy legal-entity matching. A missing alias is intentionally treated as unconfirmed.

## 11. Tests

Full golden suite:

```bash
cd backend
PYTHONPATH=. python -m evals.runner
```

Mode-specific:

```bash
PYTHONPATH=. python -m evals.runner --mode context
PYTHONPATH=. python -m evals.runner --mode agent
PYTHONPATH=. python -m evals.runner --mode rag
```

Single case:

```bash
PYTHONPATH=. python -m evals.runner --case AGENT-001
```

Targeted engineering tests:

```bash
PYTHONPATH=. python scripts/test_day6_evals.py
PYTHONPATH=. python scripts/test_day7_supplier_rag.py
PYTHONPATH=. python scripts/test_day8_structured_outputs.py
PYTHONPATH=. python scripts/test_day9_hybrid_retrieval.py
PYTHONPATH=. python scripts/test_day10_failure_modes.py
PYTHONPATH=. python scripts/test_day10_observability.py
```

Retrieval comparison:

```bash
PYTHONPATH=. python -m evals.experiments.retrieval_compare
```

## 12. Common failures

### Wrong Python environment

Symptom:

```text
(base)
.../python3.14/...
```

Fix:

```bash
conda activate supplychain-copilot
which python
python --version
```

Use Python 3.11 for the validated environment.

### `ModuleNotFoundError: No module named 'app'`

Usually caused by starting Uvicorn from the repository root.

Fix:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### Port 8000 already in use

```bash
lsof -i :8000
```

Stop stale Uvicorn processes when appropriate:

```bash
pkill -f "uvicorn"
```

### Circular import during startup

Keep these files import-light:

```text
app/agent/__init__.py
app/tools/__init__.py
```

Do not add convenience imports that recreate cycles between RAG, tools, agent, and routing modules.

### Model returns invalid JSON

The structured-output layer already parses JSON, validates Pydantic, and retries once with validation feedback.

If failures remain:

- capture raw output;
- check whether the model emits reasoning or markdown;
- confirm low temperature;
- run `test_day8_structured_outputs.py`;
- compare with the reference model.

### Supplier evidence appears for the wrong supplier

This is a critical failure.

```bash
PYTHONPATH=. python scripts/test_day7_supplier_rag.py
```

Expected behavior:

```text
resolved supplier -> supplier-filtered evidence
unresolved supplier -> no sources -> no penalty confirmation
```

### Retrieval weak after changing embeddings

Re-index the entire document collection. Do not query old document vectors using a new embedding model.

## 13. Git workflow

Recommended:

```text
main
 -> feature branch
 -> implementation
 -> targeted tests
 -> full eval
 -> pull request
 -> review
 -> merge
```

Before commit:

```bash
git status --short
git diff --stat
git diff --check
```

Before merge:

```bash
cd backend
PYTHONPATH=. python -m evals.runner
```

Generated Chroma data, local databases, uploaded documents, and evaluation reports should remain ignored unless intentionally versioned.

## 14. Development rule for AI changes

```text
change one layer
 -> run focused test
 -> run relevant eval mode
 -> run full suite
 -> inspect observability
 -> commit only after regression is understood
```

This keeps local-model experimentation attributable and disciplined.
