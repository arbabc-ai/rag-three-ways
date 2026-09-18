# RAG, three ways — a build-vs-buy case study

**One use case — "chat with your documents" (retrieval-augmented Q&A with citations) —
implemented three ways: no-code, managed-cloud, and custom. Same problem, three cost/control
trade-offs, one honest recommendation framework.**

> The thesis: the right answer to *"should we build or buy this?"* is almost never "always build"
> or "always buy." It's **"match the tool to the stakes."** This repo shows the same RAG assistant
> built at all three levels so you can see exactly what you trade at each step — and when each is
> the correct call.

Most "AI portfolio" repos show one polished build. This one shows **judgment**: the same
document-Q&A problem solved three ways, with a trade-off table grounded in real cost/latency
numbers and a decision guide. It's the artifact behind how I actually scope client work —
*don't sell custom code someone doesn't need, and don't cap a regulated workload at a no-code
tool that can't carry it.*

---

## The shared use case

A **document-grounded Q&A assistant**: point it at a corpus of PDFs/policies, ask a natural-language
question, get an answer **with citations to the source** — or an explicit **refusal** when the
documents don't support an answer. The refusal behavior matters: in every serious domain, a
confident-but-ungrounded answer is the worst failure mode.

To keep the three arms comparable, each answers the same evaluation questions over the same kind
of corpus (public regulatory text). The **custom** arm is a full regulated-domain build
([RegIntel](https://github.com/arbabc-ai/RegIntel)); the **no-code** and **managed** arms
implement the identical contract with far less code.

---

## The three builds

| | 🟢 No-code | 🟡 Managed-cloud | 🔵 Custom |
|---|---|---|---|
| **Folder** | [`01-nocode-n8n/`](01-nocode-n8n/) | [`02-managed-bedrock-kb/`](02-managed-bedrock-kb/) | [`03-custom-python/`](03-custom-python/) |
| **Stack** | n8n + Postgres/pgvector (Supabase-compatible) + local Ollama | Amazon Bedrock Knowledge Base + OpenSearch Serverless | Python: Chroma + BM25 hybrid, Titan/MiniLM, Claude |
| **Who builds it** | An operator in an afternoon | A cloud engineer in a day | An engineer over days–weeks |
| **You own** | a workflow you can edit in a GUI | AWS config (IaC) | all the code |
| **Best when** | validating an idea, low volume, SMB budget | you're already on AWS and want managed scale | you need control: custom retrieval, eval gates, regulated rigor |
| **Verified** | ✅ run end-to-end on a $0 self-hosted stack — real citation + refusal output in [its README](01-nocode-n8n/README.md#real-output) | code/IaC written, not stood up (would incur real AWS cost — see its README) | ✅ its own repo, [RegIntel](https://github.com/arbabc-ai/RegIntel), fully built and run |

Each folder has its own README, the runnable artifact (n8n workflow JSON / Terraform + boto3 /
Python package), and a "what this arm proves" note.

---

## The trade-off table (the actual decision)

Full analysis + cost model in [`docs/comparison.md`](docs/comparison.md). Summary:

| Dimension | 🟢 No-code (n8n) | 🟡 Managed (Bedrock KB) | 🔵 Custom (Python) |
|---|---|---|---|
| **Time to first answer** | hours | ~1 day | days–weeks |
| **Upfront cost** | ~$0 (OSS) + API usage | AWS setup time | engineering time |
| **Monthly floor** | low (n8n cloud ~$20 + API) | OpenSearch Serverless has a **real minimum** (~$300+/mo) | infra you choose (can be ~$0 local) |
| **Retrieval control** | vendor default | KB defaults (some knobs) | **total** (hybrid, RRF, reranking, chunking) |
| **Eval / guardrails** | bolt-on | Bedrock Guardrails (managed) | **your harness, in CI** |
| **Latency control** | limited | good | **total** |
| **Maintenance** | vendor updates can break flows | AWS-managed | you own upgrades |
| **Data residency / compliance** | depends on vendor | AWS (VPC, IAM, CloudTrail) | wherever you deploy |
| **Ceiling** | hits a wall on custom logic | scales, but you live within KB's model | **none — but you built it all** |

**The punchline:** the no-code arm is *not worse* — it's the **correct** choice for an SMB
validating an idea. The custom arm is *not over-engineering* — it's the **correct** choice for a
bank's model-risk function. The skill is knowing which line the client is actually on, and saying
so honestly.

---

## How to choose (the 30-second version)

```
Is this a throwaway prototype or a low-volume internal helper?
   └─ yes → NO-CODE (n8n/Chatbase). Ship it in an afternoon.
Already on AWS, want managed scale, standard retrieval is fine?
   └─ yes → MANAGED (Bedrock Knowledge Base). Let AWS run it.
Need custom retrieval, an eval gate, auditability, or regulated rigor?
   └─ yes → CUSTOM (own the code). Worth the weeks.
Not sure? → Start no-code to validate, port to managed/custom when a real
            constraint (control, cost-at-scale, compliance) forces the move.
```

The expensive mistake is skipping the question — building custom for a prototype (burn weeks you
didn't need) or capping a compliance workload at a no-code tool (hit a wall you can't cross).

---

## What this repo demonstrates

- **Build-vs-buy judgment**, shown not claimed — the same problem at three cost/control points.
- **Breadth across the stack** — orchestration (n8n) + managed cloud AI (Bedrock) + hand-built RAG.
- **Honest engineering economics** — a real cost model, including the Bedrock OpenSearch Serverless
  floor that surprises teams.
- **Regulated-domain depth** via the custom arm ([RegIntel](https://github.com/arbabc-ai/RegIntel)).

---

*Author: Arbab Chowdhury — pragmatic AI & data engineer, regulated financial systems + build-vs-buy
architecture. [github.com/arbabc-ai](https://github.com/arbabc-ai)*
