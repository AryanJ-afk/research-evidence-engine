### GIN index experiment: 10,000 papers

Three runs per configuration, with 100 measured requests per run.
Concurrency: 1. Result limit: 10.
Each run included one warm-up request per query.

| Configuration | Median per-run p95 | Failed requests |
|---|---:|---:|
| Without full-text index | 742.384 ms | 0/300 |
| With GIN full-text index | 173.274 ms | 0/300 |

The median per-run p95 decreased by 76.66%.

The corpus, query file, ranking, and request settings remained unchanged.
EXPLAIN ANALYZE confirmed use of papers_search_gin_idx.
A representative query returned identical papers, ordering, and scores.

These results describe a local, warmed, sequential workload using ten
diagnostic queries. They do not establish concurrent serving capacity.