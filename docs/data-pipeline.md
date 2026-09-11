# Data generation and quality

Seed 42 generates 50,000 unique payments and 4,000 synthetic customers. Two hundred duplicate raw rows are appended. The reporting year is fixed: 2025-09-11 to 2026-09-10. Reproducibility makes comparisons and screenshots stable.

## Embedded patterns
- Customer segments use different lognormal amount distributions; Enterprise payments are larger.
- Country weights differ; card payments are more common and fail more frequently than transfers.
- Spanish initial failure probability has a five-percentage-point uplift.
- German initial failure probability has a 22-point uplift from 18–25 August 2026.
- Weekend activity is weighted at 70% of weekdays; December receives a 40% uplift; modest growth is added over the year.
- Retry-eligible failures are retried with 80% probability. Second attempts succeed with 54% probability; a portion of unsuccessful second attempts proceed to a third, which succeeds with 32% probability.
- These are generation assumptions, not measured findings. The API computes measured findings from the resulting data.

## Fixed synthetic FX rates
|Currency|EUR per unit|
|---|---:|
|EUR|1|
|GBP|1.17|
|USD|0.92|
|AUD|0.61|
|SEK|0.089|

These are modeling constants, not current or historical market quotes. Local amounts are rounded to cents, then EUR values are recomputed from accepted local amounts.

## Rules
Normalize full country labels, whitespace, status casing and unambiguous date formats. Infer missing currency only from a validated country mapping. Keep the first occurrence of an ID. Reject unknown/missing customers, nonpositive/malformed amounts, invalid dates, invalid status/currency and inconsistent settlement data. Flag EUR amounts above 50,000 while retaining their financial impact; do not silently winsorize. Valid amounts are never replaced with a guessed value.

The row-level audit includes the raw CSV row number, payment ID, rule and action. Raw files remain unchanged. Corrections and rejections can overlap at a rule level, while the summary reconciles unique accepted/rejected rows. Accepted records undergo SQL constraints and post-load validation in one atomic transaction.

## Verified run
|Measure|Count|
|---|---:|
|Raw rows|50,200|
|Duplicate IDs removed|200|
|Invalid unique records rejected|230|
|Total rejected|430|
|Accepted payments|49,770|
|Corrected unique records|450|
|Outliers retained|21|
|Raw acceptance rate|99.14%|

Acceptance rate is not an independent estimate of source-data accuracy. Files under `data/raw/` and `data/clean/` are reproducible, generated locally and ignored by Git. `pipeline_runs.summary` stores the summary behind the Data Quality page.
