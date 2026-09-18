# 🟢 No-code arm — n8n + Postgres/pgvector

**Doc-Q&A with citations, built as an n8n workflow over a pgvector store — no application
code to maintain.** This is the arm you reach for to validate an idea, or to hand an SMB a working
assistant in an afternoon. **This arm has been run for real, end to end, on a $0 self-hosted
stack — see "Real output" below.**

## What's here

| File | What it is |
|---|---|
| [`workflow.json`](workflow.json) | Importable n8n workflow: webhook → embed → pgvector search → cite/refuse answer → respond |
| [`supabase_schema.sql`](supabase_schema.sql) | The `documents` table + `match_documents()` similarity-search function (standard Supabase RAG pattern; runs on any Postgres with pgvector, not only a hosted Supabase project) |
| [`docker-compose.yml`](docker-compose.yml) | Local, $0 stand-up of the whole stack: Postgres+pgvector, PostgREST (the same REST layer a hosted Supabase project runs), and n8n itself |
| [`ingest.py`](ingest.py) | The ingestion flow, done the $0-local way: fetches a real regulation from the public eCFR API, chunks it, embeds via local Ollama, inserts into `documents` |

## Why Ollama here, not OpenAI/Anthropic

The original design called for OpenAI embeddings + Claude generation, which is a completely
reasonable no-code choice — an operator adds two API keys in n8n's credential UI and is done.
But this repo's own positioning for this arm is **"SMB budget, self-host ~$0"** (see the top
README's trade-off table), and this repo already has a local model runtime proven out in
[RegIntel](https://github.com/arbabc-ai/RegIntel) (the custom arm). Swapping the two HTTP-call
nodes to hit local Ollama (`nomic-embed-text` for embeddings, `qwen2.5:7b-instruct` for
generation) instead makes the "$0" claim literal — no API key, no usage bill, nothing leaves
the machine — and is a pure node-URL change in n8n, not a different architecture. Point the
same two nodes at OpenAI/Anthropic (or Bedrock, or any other provider n8n has a credential type
for) and you're back to the original design; that's the whole point of a no-code tool.

## How it works (as verified)

```
POST /webhook/ask  {"question": "..."}
      │
      ▼
[Embed question]   HTTP → local Ollama /api/embeddings (nomic-embed-text)
      │
      ▼
[Vector search]    HTTP → local PostgREST RPC match_documents(embedding, k)   (pgvector cosine)
      │
      ▼
[Assemble context] Function node: join top-k chunks + their source labels
      │
      ▼
[Answer]           HTTP → local Ollama /api/chat, system prompt = "cite every claim; refuse if
      │                    the context doesn't support an answer"
      ▼
[Respond]          returns {answer, sources}
```

`ingest.py` is the second, near-identical flow the original README describes — kept as a
Python script rather than a second n8n workflow for this verification run, since the point being
tested is the query path's real behavior, not the ingest UI. A real deployment would build the
ingest side as its own n8n flow (read files → chunk → embed → insert) exactly as described.

## Run it (verified working, 2026-09-18)

```bash
docker compose up -d                 # Postgres+pgvector, PostgREST, n8n — all local
python3 ingest.py                    # fetches Reg WW (LCR) from eCFR, embeds via Ollama, loads it
# Import workflow.json into n8n (UI: Workflows → Import from File, or headless via CLI):
docker compose cp workflow.json n8n:/tmp/workflow.json
docker compose exec n8n n8n import:workflow --input=/tmp/workflow.json
docker compose exec n8n n8n update:workflow --id=rag3w0001 --active=true
docker compose restart n8n           # n8n CLI activation needs a restart to take effect

curl -X POST http://localhost:5678/webhook/ask -H "Content-Type: application/json" \
  -d '{"question":"What minimum liquidity coverage ratio must a covered institution maintain?"}'
```

### Real output

**An answerable question** — 287 chunks of 12 CFR Part 249 (Regulation WW, the LCR rule) were
ingested; retrieval found the operative passage and generation answered correctly with a citation:

```
$ curl -X POST http://localhost:5678/webhook/ask -H "Content-Type: application/json" \
  -d '{"question":"What minimum liquidity coverage ratio must a covered institution maintain?"}'

{"answer":"The minimum liquidity coverage ratio that a Board-regulated institution must maintain
is 1.0. [source: Regulation-WW-Liquidity-Coverage-Ratio (12 CFR Part 249)]",
 "sources":["Regulation-WW-Liquidity-Coverage-Ratio (12 CFR Part 249)"]}
```

That's the same answer [RegIntel's Phase 1](https://github.com/arbabc-ai/RegIntel) gives to the
identical question over the same regulation — good, since the whole point of this repo is that
the three arms answer the *same* contract, not that the no-code arm is a worse copy.

**A refusal case** — asked about something outside the single regulation this run ingested:

```
$ curl -X POST http://localhost:5678/webhook/ask -H "Content-Type: application/json" \
  -d '{"question":"What are the SAR filing deadlines under the Bank Secrecy Act?"}'

{"answer":"The provided sources don't contain enough information to answer that.",
 "sources":["Regulation-WW-Liquidity-Coverage-Ratio (12 CFR Part 249)"]}
```

`sources` still lists what retrieval found — vector search always returns its nearest neighbors,
even when they're not actually relevant, the same honest behavior RegIntel's Phase 3 agent
documents for its own `search_guidance` tool. The generation step is what correctly refuses
rather than stretching an unrelated chunk into an answer. Each real run took ~55–65 seconds
end-to-end on a CPU-only laptop (the embed + retrieve + generate chain, mostly the 7B generation
call) — consistent with the custom arm's own documented CPU-only latency.

## A real gotcha this run caught

The workflow originally pointed at `host.docker.internal` for both Ollama calls, which is the
standard way a Docker container reaches services on its host. It failed here with
`ECONNREFUSED` — this machine runs Ollama as a native Windows process under WSL2, and
`host.docker.internal` resolves to the WSL VM's Docker bridge gateway, which is a different
network path than the loopback-forwarding WSL2 uses to make `localhost:11434` reach Windows.
Fixed by putting the `n8n` service on `network_mode: host` in `docker-compose.yml` (true Linux
Docker networking, available because this ran on native Docker Engine, not Docker Desktop) and
pointing the workflow at plain `localhost`. On Docker Desktop (Mac/Windows) `host.docker.internal`
works normally and this isn't needed — noted in `docker-compose.yml` for whichever environment
you're running in.

## What this arm proves

- I can orchestrate a real RAG pipeline in a no-code tool — embeddings, a vector DB, and an LLM —
  and wire the **same citation/refusal contract** as the custom build, and I ran it for real
  rather than leaving it as an unexecuted workflow file.
- It's honest about the ceiling: the retrieval is pgvector's default cosine search (no BM25/hybrid,
  no reranking, no eval gate). That's *fine* for the job this arm is for — and the reason to port to
  the managed or custom arm is a **specific** need those add, not a vibe.
- PostgREST (what actually sits behind Supabase's REST API) casting a raw JSON array straight to
  a `vector` function argument, with zero glue code, is the kind of detail you only find by
  actually running the stack rather than reading Supabase's docs.

## When to choose this

Low volume, non-critical stakes, SMB budget, no engineering team, or "let's validate before we
invest." Ship in an afternoon; revisit when a real constraint appears.
