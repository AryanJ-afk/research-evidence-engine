BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE paper_embeddings (
    arxiv_id TEXT PRIMARY KEY
        REFERENCES papers(arxiv_id)
        ON DELETE CASCADE,

    embedding_model TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    embedded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT embedding_model_not_blank
        CHECK (length(trim(embedding_model)) > 0)
);

COMMIT;