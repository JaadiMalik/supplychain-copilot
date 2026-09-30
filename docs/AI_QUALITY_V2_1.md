# AI Quality v2.1 Engineering Notes

This document records the purpose of the Day 6–10 AI engineering upgrade.

It is not a user-facing changelog. It captures the engineering decisions that should remain understandable when the project is revisited or ported to another local model.

## Day 6 — Golden evaluation framework

Added `backend/evals/` with a golden dataset, intent/context/tool/retrieval/answer evaluators, report generation, and mode/case filtering.

Purpose:

> stop relying on manual demos as the only proof that the AI still works.

Reference final result:

```text
15/15 PASS
```

## Day 7 — Supplier-aware RAG

A generic RAG query could retrieve the Atlas supplier contract while evaluating an unresolved supplier. The final deterministic rule prevented incorrect qualification, but the intermediate evidence was still misleading.

Fix:

1. index supplier metadata on contract chunks;
2. derive supplier identity conservatively;
3. use explicit supplier aliases/canonical names;
4. reject placeholder supplier fields;
5. filter RAG retrieval by canonical supplier;
6. return no sources for unresolved suppliers.

Key invariant:

```text
unresolved supplier
 -> no attributed contract evidence
```

## Day 8 — Structured LLM outputs

Added Pydantic schemas for important model decisions and extracted terms.

```text
model output
 -> JSON extraction
 -> Pydantic validation
 -> one correction retry
 -> controlled failure
```

Purpose: local models can be capable but inconsistent in output structure; application code validates what it consumes.

## Day 9 — Hybrid retrieval

Added lexical scoring and reciprocal-rank fusion on top of vector search.

Modes:

```text
vector
hybrid
```

Environment selector:

```text
RAG_RETRIEVAL_MODE
```

Reference Day 9 experiment on the small current RAG test set:

```text
vector hit@5 = 100%
hybrid hit@5 = 100%
```

This did not prove that hybrid is universally superior. It established a comparison framework and preserved retrieval quality on the current set.

## Day 10 — Observability and failure handling

Added planner timing, tool timing, synthesis timing, total analysis duration, persisted status/stopped reason, an observability summary API, and targeted failure-mode tests.

Endpoint:

```text
GET /v2/observability/summary
```

Purpose: distinguish model latency from tool/RAG latency and make local-model comparisons measurable.

## Integration issue discovered

Starting the full FastAPI application exposed a circular import that standalone test paths did not reveal.

The import chain passed through:

```text
RAG
 -> agent package
 -> agent service/executor/planner
 -> tool registry
 -> supply-chain tools
 -> RAG
```

Fix:

```text
keep app/agent/__init__.py import-light
keep app/tools/__init__.py import-light
```

This is now an architecture rule.

## Final v2.1 baseline

```text
Context: 10/10 PASS
Agent:    3/3 PASS
RAG:      2/2 PASS
Full:    15/15 PASS
```

Also passing:

```text
supplier-aware RAG
structured output
hybrid retrieval smoke
failure modes
observability persistence
FastAPI startup
```

## What v2.1 does not mean

The project remains a local-first prototype/portfolio system. The current golden dataset is intentionally small.

The successful baseline means the known architecture is behaving consistently. It does not mean every supplier contract, spreadsheet, model, or deployment is production-safe.

The next important portability step is a provider-neutral model adapter while preserving these tests and deterministic business rules.
