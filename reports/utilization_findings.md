# Provider Utilization Report — implementation findings

Inspected on 2026-11-17. Implementation is pending clarification of the existing
business definition; no SQL models or Treatment Plans behavior were changed.

## Existing sources

- `models/gold_utilization/utilization.sql`: grain is client name and service-code
  group (also payment basis, usage unit and usage limit), not provider.
  `utilization = usage / usage_limit`. For HOURS, usage is the sum of
  `days_or_units * minutes_per_unit / 60.0`; for DAYS it is the sum of
  `days_or_units`. Only mapped service codes and encounters with status
  `SubmittedToClearinghouse` are included. Dates start at 2026-07-01 with no upper
  bound. The final model excludes utilization below 0.3.
- `models/bronze/alleva_service_codes.sql`: limits are service-code consumption
  limits, including both HOURS and DAYS. They are not provider available hours.
- `models/gold_utilization/forecast.sql`: appointment-based client consumption
  forecast, with ATTENDED appointments, the same fixed start and final 0.3
  filter. It also has no provider capacity definition.
- `models/gold_productivity/productivity.sql`: attended minutes by provider name,
  email and payroll period. Nonempty provider names and ATTENDED are required.
  Its Silver source excludes STAFF, non-COMPLETED and deleted appointments.
  It does not compute utilization or available hours.
- `models/bronze/backoffice_payroll_periods.sql`: inclusive start/end dates and
  payment date; no closed flag or utilization-period definition.
- `seeders/backoffice_queries/productivity_goals.sql`: employee and employment
  type, minimum_hours and effective dates. No existing model joins these goals
  to providers or establishes that minimum_hours means available capacity.

The local read-only warehouse schema confirms these distinctions. No matching
provider utilization percentage/capacity table was found. No Superset dataset,
metric or dashboard SQL definitions were found in the repository, and no
Superset connector is available in this session. Dashboard parity is therefore
not verified. Existing Utilization/productivity models have no adjacent YAML
quality rules or dedicated tests in the inspected repository.

## Decisions required

1. Supply the existing Superset provider-utilization dataset/query and metric
   definitions (including provider scope, capacity, service filters, aggregation
   and exact 50% boundary). Alternatively confirm that the intended report is
   client/service-code consumption; that would require different columns and
   must preserve the existing model's 30% visibility filter and mixed units.
2. For provider utilization, identify the approved provider identity mapping,
   capacity source, effective-date handling, zero-capacity behavior and treatment
   of providers with no attended appointments.
3. Identify the approved analysis period and closure criterion. Payroll periods
   are used for productivity, whereas current client utilization is cumulative
   from 2026-07-01. Choosing the latest payroll period with end_date before today
   would be a new report convention, not an existing utilization rule.
4. Supply the existing overall-summary aggregation: averaging percentages and
   dividing summed hours by summed capacity need not produce the same figure.

The fixed 2026-07-01 lower bound does not implement an annual reset. As requested,
no reset correction, historical recomputation or alternative period calculation
was implemented. The materialized client utilization model lacks dates needed
to select arbitrary historical windows without recomputing from underlying data.

No generator or placeholder PDF was created: the requested provider columns and
percentages cannot be derived faithfully from the current utilization model.
No dependencies were added. No pipeline, dashboard, model or orchestration
changes were made. Once the existing business definition is supplied, implement
`reports/utilization.py` with its own short-lived read-only connection and
synthetic regression tests, following Treatment Plans' independent PDF pattern.

## Scope resolved — service utilization

The user confirmed client/service-group utilization directly from Gold, strictly
above 50% (exactly 50% excluded). `reports/utilization.py` now preserves each Gold
row and its usage, limit, utilization and unit. It does not aggregate hours and
days or recompute ratios. Both consumption and limit show their unit explicitly.
The reference label mirrors the model's fixed 2026-07-01 lower bound; there is
no upper bound. `report_date` labels generation only, not a historical cutoff.
Annual reset and model freshness remain outside this generator. Superset parity
is not asserted; validation compares directly with the authoritative Gold table.
The provider-specific decisions above no longer apply to this corrected scope.
