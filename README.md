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