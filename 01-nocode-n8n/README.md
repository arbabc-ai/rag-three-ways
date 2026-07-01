# 🟢 No-code arm — n8n + Supabase (pgvector)

**Doc-Q&A with citations, built as an n8n workflow over a Supabase pgvector store — no application
code to maintain.** This is the arm you reach for to validate an idea, or to hand an SMB a working
assistant in an afternoon.

## What's here

| File | What it is |
|---|---|
| [`workflow.json`](workflow.json) | Importable n8n workflow: webhook → embed → pgvector search → cite/refuse answer → respond |
| [`supabase_schema.sql`](supabase_schema.sql) | The `documents` table + `match_documents()` similarity-search function (standard Supabase RAG pattern) |

## How it works

```
POST /webhook/ask  {"question": "..."}
      │
      ▼
[Embed question]   HTTP → OpenAI /v1/embeddings (text-embedding-3-small)
      │
      ▼
[Vector search]    HTTP → Supabase RPC match_documents(embedding, k)   (pgvector cosine)
      │
      ▼
[Assemble context] Function node: join top-k chunks + their source labels
      │
      ▼
[Answer]           HTTP → Anthropic /v1/messages, system prompt = "cite every claim; refuse if
      │                    the context doesn't support an answer"
      ▼
[Respond]          returns {answer, sources}
```

Ingestion (loading your PDFs into `documents`) is a second, near-identical flow: read files → chunk
→ embed → insert. Kept out of the request path so the same store serves many questions.

## Run it

1. **Supabase:** create a project, enable the `vector` extension, run [`supabase_schema.sql`](supabase_schema.sql) in the SQL editor.
2. **n8n:** import `workflow.json` (Workflows → Import from File).
3. **Credentials:** add your OpenAI + Anthropic + Supabase (URL + service key) credentials in n8n
   and select them on the HTTP nodes. **No keys are stored in the workflow file.**
4. Ingest a few PDFs (the ingest flow / a quick script), then `POST` a question to the webhook URL.

## What this arm proves

- I can orchestrate a real RAG pipeline in a no-code tool — embeddings, a vector DB, and an LLM —
  and wire the **same citation/refusal contract** as the custom build.
- It's honest about the ceiling: the retrieval is pgvector's default cosine search (no BM25/hybrid,
  no reranking, no eval gate). That's *fine* for the job this arm is for — and the reason to port to
  the managed or custom arm is a **specific** need those add, not a vibe.

## When to choose this

Low volume, non-critical stakes, SMB budget, no engineering team, or "let's validate before we
invest." Ship in an afternoon; revisit when a real constraint appears.
