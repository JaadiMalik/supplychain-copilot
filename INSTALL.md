# Add this documentation to the repository

The connected GitHub integration in this ChatGPT session can read the repository but currently returns HTTP 403 for repository file writes and branch creation. Use the local Git workflow below.

## 1. Sync main and create a docs branch

```bash
cd /Users/jaadimac/Documents/supplychain-copilot
git checkout main
git pull
git checkout -b docs/local-model-portability
```

## 2. Copy the documentation files

Copy the extracted bundle into the repository root so these files exist:

```text
docs/README.md
docs/architecture/SYSTEM_ARCHITECTURE.md
docs/LOCAL_MODEL_PORTABILITY.md
docs/DEVELOPMENT_GUIDE.md
docs/EVALUATION_AND_OBSERVABILITY.md
docs/AI_QUALITY_V2_1.md
```

`README_DOCS_SECTION.md` contains a section to add to the root `README.md`.

Also update visible root README version/status references from `v1.0` to `v2.1` if they are still present.

## 3. Review

```bash
git status --short
git diff --check
git diff --stat
```

## 4. Commit and push

```bash
git add README.md docs
git commit -m "docs: document architecture and local model portability"
git push -u origin docs/local-model-portability
```

Then create a pull request into `main`.

## Accuracy note

The current repository's `backend/app/config.py` uses Python constants for the LM Studio URL and model IDs. The portability guide recommends an environment/provider abstraction as a future refactor; it does not claim that abstraction already exists.
