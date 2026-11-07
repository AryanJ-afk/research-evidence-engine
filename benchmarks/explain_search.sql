EXPLAIN (ANALYZE, BUFFERS)
SELECT
    p.arxiv_id,
    p.title,
    p.abstract,
    p.authors,
    p.categories,
    p.source_updated_on,
    ts_rank(
        to_tsvector('english', p.title || ' ' || p.abstract),
        query.terms
    ) AS score
FROM papers AS p
CROSS JOIN (
    SELECT plainto_tsquery('english', 'graph decompositions') AS terms
) AS query
WHERE
    to_tsvector('english', p.title || ' ' || p.abstract)
    @@ query.terms
ORDER BY score DESC, p.arxiv_id ASC
LIMIT 10;