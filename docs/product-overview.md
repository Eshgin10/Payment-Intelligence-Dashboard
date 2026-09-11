# Payment Intelligence

An operations analyst starts with four questions: what settled, how reliably, what failed, and what retries recovered. The overview answers them without requiring a large table. Each insight opens a scoped payment explorer, where the analyst can inspect individual attempts.

## Information architecture
- Overview: four KPIs, daily settled/failed values, three SQL-derived findings, failure causes, five weakest markets, retry outcomes and five recent failures.
- Payments: server-side search, filters, 20-row pagination and an accessible detail dialog.
- Analytics: one topic at a time; markets, failures, segments, methods, daily trends and retry outcomes.
- Data Quality: raw acceptance, corrections/rejections, retained outliers and post-load SQL checks.
- Methodology: assumptions, metric definitions and engineering flow.

## Scope
This is a local-first portfolio application with a read-only product interface, not a payment processor. It has no real customer data, money movement, authentication, live FX or production monitoring. Hosting requires a Python service and PostgreSQL; the application is not represented as a static mockup or silently substituted with another database.

## Business value
Failed value helps prioritize financial impact. Country success rates locate operational friction. Retry results quantify recovery. An auditable pipeline makes the provenance of each number inspectable. These are descriptive findings, not causal claims or forecasts.
