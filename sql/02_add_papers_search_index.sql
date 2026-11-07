BEGIN;

CREATE INDEX papers_search_gin_idx
ON papers
USING GIN (
    to_tsvector('english', title || ' ' || abstract)
);

COMMIT;