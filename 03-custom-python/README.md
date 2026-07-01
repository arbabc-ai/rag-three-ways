# 🔵 Custom arm — hand-built Python RAG (RegIntel)

**The same doc-Q&A, owned end to end in code.** When you need control that the no-code and managed
arms can't give — custom hybrid retrieval, a citation/refusal contract you enforce, an eval harness
in CI, and regulated-domain rigor — you build it. This arm is a full, standalone project:

### → [github.com/arbabc-ai/RegIntel](https://github.com/arbabc-ai/RegIntel)

RegIntel is a citation-grounded RAG assistant over **banking & financial regulation** (Basel III/LCR,
FFIEC, OCC, BSA/AML). It's the "custom" end of this case study, kept as its own repo because it
stands on its own as a regulated-domain build.

## What owning the code buys you (that the other arms don't)

| Capability | Why it needs custom code |
|---|---|
| **Hybrid retrieval (dense + BM25, RRF fusion)** | Regulatory text is full of exact-term queries (`LCR`, `Regulation WW`) that pure vector search misses. No-code/managed give you dense-only defaults. |
| **Citation enforcement + refusal** | Enforced in the system prompt *and* verifiable — the worst failure in a regulated domain is a confident, ungrounded answer. |
| **An eval harness in CI** | `eval/` scores retrieval hit-rate@5 + Claude-as-judge faithfulness, so a prompt change can't silently regress quality. |
| **Swappable embeddings** | Titan on Bedrock (`USE_BEDROCK_EMBEDDINGS=1`) or local MiniLM for free/offline dev — your call, not a vendor's. |
| **Full auditability** | Every choice — chunking, retrieval, prompt, model — is in code you can review, version, and defend to a model-risk function. |

## The through-line to the other two arms

- **No-code (`01-`)** and **managed (`02-`)** implement the *same contract* (retrieve → cite →
  refuse) with far less code — correct when the stakes and volume don't justify a custom build.
- **This arm** is where you land when a *specific* need — retrieval quality, an eval gate,
  compliance, or it being core IP — actually forces owning the stack.

That progression **is** the build-vs-buy thesis: start as light as the problem allows, and step up
only when a real constraint makes you. See [`../docs/comparison.md`](../docs/comparison.md).
