# research-evidence-engine

## Initial ingestion observation

- Workload: first 1,000 papers matching the target categories, in source order.
- Method: one parameterized upsert per paper, using one connection and one transaction.
- Processed: 1,000 papers.
- Elapsed time: 1.06 seconds in a single local run.
- Database afterward: 1,000 target papers and one physics test paper.
- Cache conditions: not controlled.

## Start the API locally

With the virtual environment active and PostgreSQL running, run from the repository root:

```bash
python -m uvicorn app.main:app --reload
```


## Keyword search scaling baseline

- Corpus: 10,000 target papers plus one physics test paper.
- Ingestion: 10,000 upserts completed in 6.19 seconds in one local run.
- Benchmark: six fixed queries, one warmup and 20 measured runs per query.
- Each measured search opens and closes a database connection.
- Median latency increased from 83.38–92.95 ms at 1,001 papers
  to 422.66–498.15 ms at 10,001 papers.
- EXPLAIN ANALYZE showed a parallel sequential scan for
  "learning algorithms", with text vectors computed during the query.
- Reports are saved in benchmarks/results/.