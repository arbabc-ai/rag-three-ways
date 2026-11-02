# rag-three-ways — Claude Code notes
_Draft by Claude, 2026-11-01 — edit to your own wording._

Build-vs-buy case study: one document-Q&A use case built three ways (no-code n8n, managed Bedrock KB, custom Python = RegIntel). PUBLIC repo.

## Commands (02-managed-bedrock-kb/README.md; no CI)
- Managed arm query: `export KB_ID=...` then `python query.py "<question>"` (in `02-managed-bedrock-kb/`)
- Infra is `02-managed-bedrock-kb/main.tf` (`terraform init && terraform apply` per its README) — see rules
- `03-custom-python/` is only a README pointing to the RegIntel repo

## Key paths
- `01-nocode-n8n/` — `workflow.json`, `supabase_schema.sql`
- `02-managed-bedrock-kb/` — `main.tf`, `query.py`
- `docs/comparison.md` — trade-off/cost analysis

## Rules
- Never run `terraform apply` or `terraform destroy` without explicit approval (OpenSearch Serverless has a real monthly cost floor).
- Public repo: never commit `.env*`, keys, `*.tfstate*`, `.terraform/`, `data/raw`, chroma stores, `*.pkl` (see `.gitignore`). A local pre-commit hook (`.git/hooks/pre-commit` → `~/.claude/bin/secret-scan-staged.sh`) blocks staged secrets, `.env` files and data; `.claude/settings.json` denies reading/editing `.env`. Bypass only deliberately with `git commit --no-verify`.
- Local commits only; no push unless asked.
