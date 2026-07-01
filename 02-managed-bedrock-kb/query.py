#!/usr/bin/env python3
"""Query a Bedrock Knowledge Base with RetrieveAndGenerate — the managed RAG arm.

The managed equivalent of the custom arm's retrieve + generate + cite: one API call does
retrieval, prompt assembly, generation, and returns citations. AWS runs the vector store.

Usage:
    export KB_ID=xxxxxxxxxx
    export AWS_REGION=us-east-1
    python query.py "What minimum LCR must a covered institution maintain?"

Requires: boto3, AWS credentials, and Bedrock model access (Titan + a Claude model) — the
same setup as AIF-C01.
"""
from __future__ import annotations

import os
import sys

import boto3

REGION = os.environ.get("AWS_REGION", "us-east-1")
KB_ID = os.environ.get("KB_ID")
# Claude on Bedrock. Swap the model id for whatever you've been granted access to.
MODEL_ARN = os.environ.get(
    "MODEL_ARN",
    f"arn:aws:bedrock:{REGION}::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
)


def ask(question: str) -> dict:
    if not KB_ID:
        raise SystemExit("Set KB_ID (your Bedrock Knowledge Base id).")

    client = boto3.client("bedrock-agent-runtime", region_name=REGION)
    resp = client.retrieve_and_generate(
        input={"text": question},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KB_ID,
                "modelArn": MODEL_ARN,
                "retrievalConfiguration": {
                    "vectorSearchConfiguration": {"numberOfResults": 5}
                },
                # A grounding/refusal instruction — the managed analogue of the custom
                # arm's system prompt. Pair with Bedrock Guardrails for hard enforcement.
                "generationConfiguration": {
                    "promptTemplate": {
                        "textPromptTemplate": (
                            "You answer using only the search results below. Cite each claim. "
                            "If they don't support an answer, say you don't have enough "
                            "information — do not guess.\n\n$search_results$\n\n"
                            "Question: $query$"
                        )
                    }
                },
            },
        },
    )

    # Citations map answer spans back to the S3 source documents.
    sources = []
    for citation in resp.get("citations", []):
        for ref in citation.get("retrievedReferences", []):
            loc = ref.get("location", {}).get("s3Location", {}).get("uri")
            if loc and loc not in sources:
                sources.append(loc)

    return {"answer": resp["output"]["text"], "sources": sources}


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What minimum liquidity coverage ratio must a covered institution maintain?"
    result = ask(q)
    print("\n=== ANSWER ===")
    print(result["answer"])
    print("\n=== SOURCES ===")
    for s in result["sources"]:
        print(f"  - {s}")
    if not result["sources"]:
        print("  (none — the KB returned no grounded citation; treat as a refusal)")
