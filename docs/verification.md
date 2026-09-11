# Verification record

Verified locally on 11–12 September 2026 against PostgreSQL 17.11 and the generated synthetic dataset.

## Automated
- Twelve pytest tests passed: cleaning/audit reconciliation, generator reproducibility, invalid records, retained outliers, known-value SQL metrics, retry value, pagination, search, inclusive dates, zero filling, input validation, empty denominators and unknown payment responses.
- PostgreSQL load: 49,770 payments accepted; all five post-load quality queries returned zero violations.
- Next.js production compilation, TypeScript validation and route generation passed.
- Live API default-period totals matched the values displayed in the dashboard.

## Browser
- Overview loaded live PostgreSQL data.
- 7D changed the date range, payment count, volume, success and insights.
- Country drill-down preserved the selected reporting period and country.
- Payment detail rendered local amount, EUR amount, merchant, customer and attempt/settlement timeline.
- Escape dismissed the detail dialog and restored the payment explorer.
- A nonexistent search returned an explicit no-results state.
- Analytics topic switching and country selection returned the selected country's performance.
- Data Quality matched the stored pipeline summary and five passing SQL checks.
- Desktop and narrow mobile layouts inspected. Tables and navigation scroll inside their own containers.
- The 390px production view has no page-level horizontal overflow after containing hidden table labels.
- Optional WebMCP `read_payment_view` returned the current view and filters; invalid extra input was intentionally rejected.

## Limits
Docker is not installed here, so Compose/Dockerfiles are not runtime-tested. No external deployment or public repository was created. No claim of exhaustive accessibility certification or load testing is made.
