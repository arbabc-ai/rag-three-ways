# The comparison — cost, control, and when to choose which

This is the analysis behind the summary table in the [top README](../README.md). It exists because
"which one should we use?" is a real client question with a real dollar answer, and the honest
answer depends on stakes and scale — not fashion.

## The same contract, three implementations

All three arms satisfy the identical behavioral contract, so the comparison is apples-to-apples:

1. **Ingest** a corpus of documents (PDF/text) → chunk → embed → store in a vector index.
2. **Retrieve** the top-k relevant chunks for a question.
3. **Generate** an answer that **cites its sources**, and **refuses** when retrieval returns nothing
   relevant (no hallucinated answers).
4. Be **evaluable** — you can measure retrieval quality and answer faithfulness.

What differs is *who* implements each step and *how much* you can change it.

---

## Cost model (illustrative, ~1,000 documents, ~2,000 questions/month)

Numbers are order-of-magnitude to reason with, not quotes — real cost depends on region, model,
and volume. The point is the **shape** of each curve.

| Cost component | 🟢 No-code (n8n + Supabase) | 🟡 Managed (Bedrock KB) | 🔵 Custom (Python) |
|---|---|---|---|
| Platform floor | n8n Cloud ~$20–50/mo (or self-host ~$0) | **OpenSearch Serverless ~$300+/mo minimum** (2 OCUs) | $0 local / your infra if deployed |
| Vector store | Supabase free–$25/mo | included in the OpenSearch floor | Chroma (free, local) or pgvector |
| Embeddings | API per token (~$0.02/1M, Titan/OpenAI) | Titan, per token | Titan (paid) or MiniLM (free, local) |
| Generation | Claude/GPT per token | Claude on Bedrock per token | Claude per token |
| **Effective monthly floor** | **~$20–75** | **~$300+ before a single query** | **~$0–50** |
| **Marginal cost / 1k questions** | low (API only) | low (API only) | low (API only) |

**The number that surprises teams:** Bedrock Knowledge Base is "managed," but its default vector
store — **OpenSearch Serverless — bills a minimum of ~2 OCUs (~$300+/month) whether you ask one
question or a million.** For a high-volume production workload that's nothing; for a prototype or a
low-traffic internal tool it's a poor fit. This single fact flips many "just use the managed
service" defaults, and it's exactly the kind of thing a client is glad you flagged *before* the
first invoice. (Bedrock now offers cheaper vector backends like Aurora pgvector / S3 Vectors —
noted in the managed arm's README — but OpenSearch Serverless is the path most tutorials show.)

---

## Control: what you can change at each level

| You want to change… | 🟢 No-code | 🟡 Managed | 🔵 Custom |
|---|---|---|---|
| Chunking strategy | ❌ vendor default | ⚠️ a few presets | ✅ any (recursive, semantic, per-doc) |
| Retrieval algorithm | ❌ | ⚠️ dense (+ optional hybrid) | ✅ dense + BM25 + RRF + rerank |
| Embedding model | ⚠️ pick from list | ⚠️ pick from list | ✅ any, incl. local/offline |
| Prompt & refusal logic | ✅ editable in GUI | ✅ editable | ✅ full control |
| Guardrails | ⚠️ bolt-on | ✅ Bedrock Guardrails (managed) | ✅ your own + Guardrails |
| Eval in CI | ❌ | ⚠️ external | ✅ native (`eval/` harness) |
| Custom business logic | ⚠️ within node limits | ⚠️ within KB model | ✅ unlimited |

The pattern: **each step up buys control and costs effort.** No-code trades control for speed;
custom trades speed for control; managed sits in between and trades *both* for AWS operating it.

---

## Maintenance & risk

- **No-code:** fastest to stand up, but a vendor UI/node update can silently break a flow, and
  complex logic becomes a spaghetti of nodes that's hard to review or version like real code.
- **Managed:** AWS patches and scales it, but you're bounded by the KB's model of the world; when
  you need something it doesn't do, you're stuck or you're porting.
- **Custom:** no ceiling and fully testable/versionable, but every dependency upgrade, security
  patch, and scaling decision is yours.

---

## Decision framework

```
1. What are the stakes if an answer is wrong?
     low (internal helper)        → no-code is fine
     high (customer/regulated)    → managed or custom (need guardrails + eval + audit)

2. What volume / latency do you need?
     spiky / low                  → no-code or custom-local (don't pay a managed floor)
     steady / high                → managed (let AWS scale) or custom (if you have the team)

3. How much does retrieval quality matter?
     "good enough"                → no-code / managed defaults
     "must tune recall & precision" → custom (hybrid + rerank + eval loop)

4. Compliance / data residency?
     none                         → cheapest that works
     strict (bank, health)        → managed-in-VPC or custom-in-your-account, with IAM + audit

5. Team & timeline?
     no engineers / this week     → no-code
     cloud team / this month      → managed
     engineers / it's core IP     → custom
```

**Default recommendation for most SMBs:** start **no-code** to validate the use case cheaply, and
port to **managed** or **custom** only when a specific constraint — cost-at-scale, retrieval
quality, latency, or compliance — actually forces the move. Premature custom-building is the most
common (and expensive) mistake I'm hired to unwind.

---

## How this maps to the three arms in this repo

- [`01-nocode-n8n/`](../01-nocode-n8n/) — the importable n8n workflow + Supabase schema.
- [`02-managed-bedrock-kb/`](../02-managed-bedrock-kb/) — Terraform/boto3 to stand up the KB + a
  `retrieve_and_generate` query script.
- [`03-custom-python/`](../03-custom-python/) — the full custom build ([RegIntel](https://github.com/arbabc-ai/RegIntel)):
  hybrid retrieval, citation/refusal, and an eval harness in code.
