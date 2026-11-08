# Evaluation review: test-v1-run1

Dataset: evaluation/test_cases.jsonl
Run: evaluation/results/test-v1-run1.jsonl

## Method

An answerable case passes only if it answers the question correctly, supports every factual claim with its citations, and preserves the
sources' conditions, uncertainty, and scope.

## Results

| Metric | Result |
|---|---|
| Completed requests | 30/30 |
| Known-evidence context hits | 20/20 |
| Supported-answer success | 17/20 (85%) |
| Correct abstentions | 10/10 |
| Expected answer-or-abstain decisions | 30/30 |

## Unsuccessful answerable cases

- test-01: Answers the core question but combines details from different
  experimental setups without clearly distinguishing their scope.
- test-04: Correct temperature comparison, but presents a proposed
  explanation too definitively.
- test-06: Correctly distinguishes possibility from certainty, but
  describes historical observational constraints as current.

The remaining 17 answerable cases passed the review.

## Limitations

This is a small, custom, assistant-drafted evaluation set reviewed
against the abstracts. It measures one run, primarily on questions
answerable from individual abstracts. It does not establish performance on arbitrary research questions or full-paper synthesis.

Any subsequent tuning using these results makes this a development
benchmark rather than an untouched test set.