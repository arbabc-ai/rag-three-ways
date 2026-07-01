# 🟡 Managed-cloud arm — Amazon Bedrock Knowledge Base

**The same doc-Q&A, but AWS runs the retrieval layer.** You point a Bedrock Knowledge Base at an S3
bucket of documents; it chunks, embeds (Titan), stores vectors, and answers via `RetrieveAndGenerate`
— with **Bedrock Guardrails** for grounding/refusal. You own configuration (IaC), not code.

## What's here

| File | What it is |
|---|---|
| [`query.py`](query.py) | Runnable: calls `bedrock-agent-runtime.retrieve_and_generate` against your KB — returns a cited answer |
| [`main.tf`](main.tf) | Terraform skeleton for the core resources (S3 data source, KB, data source, model wiring) |

## How it works

```
S3 (your PDFs)  ──►  Bedrock Knowledge Base  ──►  vector store (OpenSearch Serverless / Aurora / S3 Vectors)
                          │  (chunk + Titan embed, managed)
                          ▼
   query.py ──►  RetrieveAndGenerate(kbId, model)  ──►  cited answer  ( + Bedrock Guardrails: grounding/refusal )
```

You configure the pieces; AWS operates them. Retrieval, chunking, and scaling are managed — you tune
via settings, not code.

## Run it

Prereq: AWS account with **Bedrock model access** granted (Titan Embeddings + a Claude model) — the
same access you set up for AIF-C01.

```bash
pip install boto3
export KB_ID=xxxxxxxxxx                 # from the console or `terraform output`
export AWS_REGION=us-east-1
python query.py "What minimum LCR must a covered institution maintain?"
```

Stand up the KB either in the **console** (Bedrock → Knowledge Bases → Create — fastest) or via
[`main.tf`](main.tf) (`terraform init && terraform apply`), then sync the data source.

## ⚠️ The cost gotcha (say this to the client before they build)

Bedrock KB's most-documented vector store, **OpenSearch Serverless, bills a ~2-OCU minimum
(~$300+/month)** whether you run one query or a million. For production volume that's noise; for a
prototype or low-traffic internal tool it's the wrong default. Cheaper backends now exist —
**Aurora PostgreSQL (pgvector)** and **S3 Vectors** — and `main.tf` notes where to swap. Flagging
this *before* the first invoice is exactly the build-vs-buy judgment this repo is about.

## What this arm proves

- I can stand up managed cloud AI infra (Bedrock KB + a vector store + Guardrails) as **IaC**, and
  query it programmatically — reusing the AIF-C01 Bedrock foundation.
- Honest trade: less control than the custom arm (chunking/retrieval are KB's model), higher floor
  than no-code — bought in exchange for AWS operating it at scale with IAM + CloudTrail + VPC.

## When to choose this

You're already on AWS, want managed scale and standard retrieval, and the volume justifies the
floor. Not for throwaway prototypes (pay-to-play minimum) or for workloads needing custom retrieval
/ an eval gate (that's the custom arm).
