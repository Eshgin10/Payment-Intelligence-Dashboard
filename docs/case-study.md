# Payment Intelligence · case study narrative

## Problem
Payment teams need to separate throughput from unrecovered loss. A single success percentage hides market-level problems, failure causes and the value of retrying eligible payments.

## Data requirements
Model payments as business entities with separate attempt histories. Retain the customer segment, country, method, merchant, initial failure, final outcome and comparable EUR value. Keep provenance through ingestion.

## Dataset and cleaning
Generate realistic differences in activity, amounts and failure probabilities. Inject known defects, preserve raw files, log deterministic repairs, reject impossible records and retain outliers transparently. Load 49,770 accepted payments into a constrained relational schema.

## SQL analysis
Answer gross settlement, final success, failed value and recovery questions using SQL. Compare equal windows, fill missing days, rank markets and calculate failure-value shares. Avoid cross-currency summation and duplicate recovery counting.

## UX decision
Put four outcomes first. Give the largest chart the most space. Present three explanatory findings in a contrasting panel. Move broad exploration into focused topic tabs and record-level detail into a drawer. Make data quality an equal navigation destination.

## Business value
The analyst can move from an issue to the affected payments in one click. A market insight retains its period and country. The detail panel explains whether retries occurred and what they achieved. A separate quality audit explains which source records reached the dashboard.

## Evidence for publication
Use the verified screenshots alongside the SQL files, known-value tests and pipeline summary. Distinguish generation assumptions from measured outcomes. Present this as a working synthetic-data portfolio application; do not imply real business impact, real customers or a public production deployment.
