# Payment Intelligence · brand and product system

The supplied brand manual is the primary identity reference. The Lumin and Fingoals dashboards inform spacing, hierarchy and rounded controls; their logos and brand names are not reused.

## User and hierarchy
Operations analysts need to identify loss, understand its source, and inspect the affected payments. Overview → Analytics → Payments is the primary investigation flow. Data Quality establishes trust; Methodology explains the portfolio implementation.

## Visual thesis
An editorial financial workspace: generous warm-white space, precise charcoal typography and sparing electric-green punctuation. A charcoal insights column is the distinctive anchor. Green always has dark text; never use green body text on white.

Tokens: accent #78FF00; ink #202020; canvas #F5F5F2; surface #FFFFFF; muted #666861; border #E5E6E0. Font: system sans-serif, using Inter when installed. Spacing: 4/8/12/16/24/32/48px. Radius: 12px controls, 20px panels, pill navigation. Minimal shadows. Labels 14px; body 16px; metadata 12px. Focus rings are charcoal with a white offset.

## Desktop wireframe
```
mark + product     Overview / Payments / Analytics / Quality / Methodology
Page heading                                         date controls
Processed volume | Payment success | Failed value | Recovered value
Performance time series (2/3)          | charcoal insights (1/3)
Failure value bars                    | country success rankings
Retry effectiveness
Notable payments (five rows)
```

Mobile wraps navigation, stacks panels and uses a two-column metric group (one column on narrow screens). Tables scroll inside their container. Charts carry units, legends, tooltips and accessible text summaries. Insight actions pass a country or failure filter into the payments explorer.

## Components and states
Button, Select, DatePicker, Metric, ChartContainer, Badge, DataTable, Tooltip, FilterBar, Insight, EmptyState, ErrorState and LoadingState share the same tokens. Errors offer retry; no results explain the current filter scope. Loading uses skeletons. Detail dialogs trap focus and close with Escape. Synthetic dataset disclosure remains visible throughout.
