# Contributing to Hakiki

Thank you for helping. A few rules keep the project trustworthy, because it handles claims for a health fund.

## Ground rules

- **Synthetic data only.** Never commit real patient data, real claim exports or secrets. CI runs gitleaks on every push.
- **Branch and pull request.** Nobody pushes to `main`. CI must be green before merging.
- **Tests with every change.** A change without a test is not done.
- **Every rule keeps its citation.** A rule in `kb/rules/` needs a quote and a source in `kb/citations.json`. Mark a quote `verified` only after checking it against the document in `docs/sources/`.
- **The LLM never decides.** Verdicts come from the MeTTa rules. The narrator only rephrases a finished trace.
- **Keep the style.** No comments unless they explain something non-obvious. Match the code around you.

## Set up

```bash
python3.12 -m venv .venv && source .venv/bin/activate      # hyperon needs Python 3.12
pip install -r requirements-dev.txt
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis
alembic upgrade head
ruff check . && ruff format . && pytest
cd dashboard && npm install && npm test
```

`./scripts/demo.sh` starts the whole stack in containers with a seeded demo login.

## Changing the API

Run `python -m scripts.export_openapi` and commit `docs/openapi.json`. A test fails when it is out of date, and `dashboard/src/types.ts` must match.

## Changing a rule or a truth value

1. Edit the rule in `kb/rules/` and its entry in `kb/citations.json`.
2. Update `kb/rules/truth-values.md` when a strength or confidence changes.
3. Regenerate the golden traces, since trace hashes change when rules or truth values do.
4. Bump `kb/VERSION`.

## Licences

Code is MIT. Files in `kb/` are CC BY 4.0. By contributing you agree to those terms.
