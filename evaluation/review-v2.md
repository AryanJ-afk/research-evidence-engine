# Evaluation review: test-v2-run1

Dataset: evaluation/test_cases.jsonl
Run: evaluation/results/test-v2-run1.jsonl
Baseline: evaluation/results/test-v1-run1.jsonl

## Method

This is a development-set comparison: the baseline failures informed the prompt changes.

## Results

| Metric | Baseline | Revised prompt |
|---|---|---|
| Supported-answer success | 17/20 (85%) | 18/20 (90%) |
| Known-evidence context hits | 20/20 | 20/20 |
| Correct abstentions | 10/10 | 10/10 |
| Request errors | 0/30 | 0/30 |

## Findings

- test-04 improved: the answer omits the overstated explanation.
- test-01 remains unsuccessful: different experimental setups are
  combined without sufficiently clear attribution.
- test-06 remains unsuccessful: historical observations are still
  described using ambiguous present-day language.
- No clear new failures were identified in the other 17 answerable cases.

## Interpretation

Supported-answer success increased by 5 percentage points in this
single before/after comparison. Model variability and the small,
custom development set limit conclusions about general improvement.