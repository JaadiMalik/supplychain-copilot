# Evaluation and Observability

## 1. Why evaluation is part of the product

Local models can appear correct during a manual demo and still fail on JSON formatting, tool selection, SQL generation, evidence isolation, supplier identity, retrieval, or unsupported questions.

The repository therefore keeps a small golden evaluation suite.

Use it whenever changing:

- generation model;
- embedding model;
- model quantization;
- inference runtime;
- prompts;
- retrieval strategy;
- structured-output schemas;
- agent planning logic.

## 2. Golden dataset

Current set:

```text
10 context cases
3 agent cases
2 RAG cases
15 total
```

Dataset:

```text
backend/evals/datasets/supplychain_golden.json
```

Evaluators cover intent, resolved context, tool use, retrieval, and answer behavior.

## 3. Running evaluations

From `backend`:

```bash
PYTHONPATH=. python -m evals.runner
```

Filter by mode:

```bash
PYTHONPATH=. python -m evals.runner --mode context
PYTHONPATH=. python -m evals.runner --mode agent
PYTHONPATH=. python -m evals.runner --mode rag
```

Single case:

```bash
PYTHONPATH=. python -m evals.runner --case AGENT-001
```

Reports are written under:

```text
backend/evals/reports/
```

These are runtime artifacts and need not be committed.

## 4. Current reference baseline

At the v2.1 AI-quality milestone:

```text
Context: 10/10 PASS
Agent:    3/3 PASS
RAG:      2/2 PASS
Total:   15/15 PASS
```

This is a regression baseline, not proof of production readiness.

## 5. Targeted regression tests

Supplier-aware RAG:

```bash
PYTHONPATH=. python scripts/test_day7_supplier_rag.py
```

Structured outputs:

```bash
PYTHONPATH=. python scripts/test_day8_structured_outputs.py
```

Hybrid retrieval:

```bash
PYTHONPATH=. python scripts/test_day9_hybrid_retrieval.py
```

Failure modes:

```bash
PYTHONPATH=. python scripts/test_day10_failure_modes.py
```

Observability persistence:

```bash
PYTHONPATH=. python scripts/test_day10_observability.py
```

## 6. Retrieval experiment

```bash
PYTHONPATH=. python -m evals.experiments.retrieval_compare
```

At the Day 9 milestone, the small current RAG test set produced:

```text
vector hit@5: 100%
hybrid hit@5: 100%
```

Observed mean retrieval timing in that run:

```text
vector: 5.21 ms
hybrid: 3.34 ms
```

Do not conclude from this small run that hybrid retrieval is always faster. The meaningful result is that hybrid retrieval preserved hit@5 while changing ranking behavior.

As the corpus grows, add more contracts, suppliers, exact identifiers, percentages, conflicting clauses, similarly named suppliers, and negative/no-answer queries.

## 7. Agent latency

Agent latency varied substantially across local runs because generation is local and combined analysis can require multiple model calls.

Observed individual `AGENT-001` runs during development were on the order of tens of seconds, including runs around 46–71 seconds.

Do not use the full-suite median as the agent latency baseline because many context cases are deterministic and extremely fast.

Track AI-heavy modes separately.

## 8. Observability model

The agent records analysis events in DuckDB.

Important fields:

```text
analysis_id
status
duration_ms
rounds_used
stopped_reason
planner_duration_ms
tool_duration_ms
synthesis_duration_ms
created_at
```

Endpoint:

```text
GET /v2/observability/summary
```

Example:

```bash
curl http://127.0.0.1:8000/v2/observability/summary
```

## 9. Why timing is split

A slow answer can come from different layers:

```text
planner
tool execution
retrieval
SQL
contract extraction
final synthesis
```

Use the split to determine whether a candidate local model is slow at planning, extraction, or synthesis rather than assuming all latency comes from the model itself.

## 10. Model-swap acceptance gate

Before adopting another local generation model:

```bash
PYTHONPATH=. python scripts/test_day8_structured_outputs.py
PYTHONPATH=. python scripts/test_day10_failure_modes.py
PYTHONPATH=. python -m evals.runner --mode agent
PYTHONPATH=. python -m evals.runner
```

Before adopting another embedding model, additionally run:

```bash
PYTHONPATH=. python scripts/test_day7_supplier_rag.py
PYTHONPATH=. python scripts/test_day9_hybrid_retrieval.py
PYTHONPATH=. python -m evals.experiments.retrieval_compare
PYTHONPATH=. python -m evals.runner --mode rag
```

Comparison record:

| Check | Reference | Candidate |
|---|---|---|
| Context | 10/10 | |
| Agent | 3/3 | |
| RAG | 2/2 | |
| Full suite | 15/15 | |
| Supplier isolation | PASS | |
| Structured output | PASS | |
| Failure modes | PASS | |
| Retrieval hit@5 | 100% on current set | |
| Agent latency | local baseline | |
| Memory use | local measurement | |

## 11. When a candidate model fails

Classify the failure before changing prompts:

```text
A. runtime/API mismatch
B. response parsing mismatch
C. JSON/schema failure
D. planning/tool-selection failure
E. SQL-generation failure
F. retrieval failure
G. evidence extraction failure
H. final synthesis failure
```

Then make the smallest targeted change and rerun the relevant tests.

## 12. Expanding the suite

Every meaningful production-like failure should become a regression case.

Good future cases:

- supplier alias missing;
- two similarly named suppliers;
- two contracts with similar penalty language;
- contract with no penalty;
- contract with exceptions but no rate;
- open PO for unresolved supplier;
- closed PO for confirmed supplier;
- exact contract ID query;
- exact percentage query;
- malformed model JSON;
- planner selects unknown tool;
- embedding runtime unavailable;
- generation runtime unavailable.
