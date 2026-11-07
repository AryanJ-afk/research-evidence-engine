BEGIN;

CREATE TABLE papers (
    arxiv_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT NOT NULL,
    authors TEXT NOT NULL,
    categories TEXT[] NOT NULL,
    source_updated_on DATE NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT papers_id_not_blank
        CHECK (length(trim(arxiv_id)) > 0),

    CONSTRAINT papers_title_not_blank
        CHECK (length(trim(title)) > 0),

    CONSTRAINT papers_abstract_not_blank
        CHECK (length(trim(abstract)) > 0)
);

COMMIT;