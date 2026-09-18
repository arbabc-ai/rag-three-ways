"""Ingestion for the no-code arm's local, verified run.

The README calls ingestion "a second, near-identical flow" to the query
webhook, kept out of n8n on purpose (load-once, query-many). This script is
that flow, done the $0-local way: fetch a real regulation from the public
eCFR API (same corpus family as the custom arm, RegIntel), chunk it, embed
each chunk with local Ollama (nomic-embed-text), and insert into the
`documents` table docker-compose.yml stands up.

Run: python3 ingest.py   (after `docker compose up -d`)
"""
from __future__ import annotations

import re
import subprocess

import httpx

OLLAMA_HOST = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
PG_DSN = "postgresql://raguser:ragpass@localhost:55432/ragdb"

# 12 CFR Part 249 — Regulation WW (Liquidity Coverage Ratio). Same regulation
# the managed arm's own example query asks about, so the three arms stay
# comparable on the same underlying source text.
SOURCE_LABEL = "Regulation-WW-Liquidity-Coverage-Ratio (12 CFR Part 249)"
ECFR_URL = (
    "https://www.ecfr.gov/api/renderer/v1/content/enhanced/current/"
    "title-12?chapter=II&subchapter=A&part=249"
)

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def _strip_html(text: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.S | re.I)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _chunk(text: str, size: int, overlap: int) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


def _embed(text: str) -> list[float]:
    resp = httpx.post(
        f"{OLLAMA_HOST}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60.0,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def _sql_literal(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def main() -> None:
    print(f"Fetching {SOURCE_LABEL} from eCFR...")
    resp = httpx.get(ECFR_URL, timeout=60.0, follow_redirects=True)
    resp.raise_for_status()
    text = _strip_html(resp.text)
    print(f"  {len(text)} chars of clean text")

    chunks = _chunk(text, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"  {len(chunks)} chunks ({CHUNK_SIZE}/{CHUNK_OVERLAP})")

    values = []
    for i, chunk in enumerate(chunks):
        embedding = _embed(chunk)
        vec_literal = "'[" + ",".join(str(x) for x in embedding) + "]'"
        values.append(
            f"({_sql_literal(chunk)}, {_sql_literal(SOURCE_LABEL)}, {i}, {vec_literal}::vector)"
        )
        if (i + 1) % 10 == 0 or i == len(chunks) - 1:
            print(f"  embedded {i + 1}/{len(chunks)}")

    sql = (
        "delete from documents;\n"
        "insert into documents (content, source, chunk_index, embedding) values\n"
        + ",\n".join(values)
        + ";\n"
    )
    result = subprocess.run(
        ["psql", PG_DSN, "-v", "ON_ERROR_STOP=1"],
        input=sql,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise SystemExit("psql insert failed")
    print(f"Inserted {len(chunks)} chunks into `documents`.")


if __name__ == "__main__":
    main()
