-- pgvector schema for the no-code RAG arm.
-- Run in the Supabase SQL editor for a hosted project, or (as this repo's
-- verified local run does) against any Postgres with the pgvector extension —
-- docker-compose.yml mounts this file to auto-run on container init.

-- 1. Enable pgvector (Supabase ships it; this is idempotent).
create extension if not exists vector;

-- 2. Chunk store. 768 dims = Ollama nomic-embed-text (this repo's verified
--    local run). Use 1536 for OpenAI text-embedding-3-small, or 1024 for
--    Amazon Titan v2, if you swap the embedding step back to a hosted API.
create table if not exists documents (
    id          bigint generated always as identity primary key,
    content     text        not null,          -- the chunk text
    source      text        not null,          -- source doc label, e.g. 'basel_iii_lcr.pdf'
    chunk_index int         not null default 0,
    embedding   vector(768),
    created_at  timestamptz not null default now()
);

-- 3. Approximate-nearest-neighbour index for fast cosine search at scale.
create index if not exists documents_embedding_idx
    on documents using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

-- 4. Similarity search function called by the n8n "Vector search" node.
--    Returns the top-k chunks plus a cosine similarity score.
create or replace function match_documents (
    query_embedding vector(768),
    match_count     int default 5
)
returns table (
    id         bigint,
    content    text,
    source     text,
    similarity float
)
language sql stable
as $$
    select
        d.id,
        d.content,
        d.source,
        1 - (d.embedding <=> query_embedding) as similarity   -- <=> = cosine distance
    from documents d
    order by d.embedding <=> query_embedding
    limit match_count;
$$;
