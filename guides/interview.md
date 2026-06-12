# Domain Expert Interview Guide

How to interview metric owners and senior analysts to fill the schema fields that documents rarely contain.

Use this after running the [distillation prompt](distillation-prompt.md) and doing any available warehouse preflight (see [sourcing.md](sourcing.md)). The goal is not to ask every question in one sitting. Start with the fields marked `# NOT FOUND`, `# NEEDS REVIEW`, or `# CONFLICT`, then ask the smallest set of follow-ups needed to turn the draft into reviewable YAML.

For each answer, capture the exact field it supports and the evidence source: interviewee name or role, date, and any linked doc, query, dashboard, incident, contract, or Slack thread.

## Interview Setup

Before the interview:

- Bring the current metric YAML and draft `meta:` block.
- Highlight missing or uncertain fields by layer.
- Bring the Layer 2 warehouse preflight output if available: trailing 12-month range, volatility, trend, segment cuts, and obvious outliers.
- Tell the expert you are not asking for general education. You are filling specific context-card fields that an AI agent will read later.

During the interview:

- Ask conversationally, not as a form.
- Push for magnitude, ordering, thresholds, owners, and exceptions.
- Convert anecdotes into fields. A story about "the November outage" likely belongs in `known_root_causes`; a contract caveat likely belongs in `business_rules`.

## Layer 1: Context

Question: "When different teams say this metric's name, are they always talking about the same population, time grain, and definition?"

Listen for:

- `definition` boundaries: included and excluded populations, windows, statuses, or lifecycle stages.
- `aliases` used by sales, finance, product, support, or operations.
- Similar metrics that are easy to confuse with this one.

Question: "Who has authority to approve a definition change, and who would be surprised or affected if it changed?"

Listen for:

- `owner` as the accountable team or role, not just the person who built the dbt model.
- `stakeholders` who consume, fund, audit, or are measured by the metric.
- Review or notification expectations that may also feed Layer 5.

Question: "What business question should this metric answer that the SQL formula alone does not make obvious?"

Listen for:

- `purpose` phrased in business terms, not implementation terms.
- `business_question` tied to a real decision or monitoring workflow.
- Scope limits where the right answer is "this metric cannot answer that."

## Layer 2: Expectations

Question: "Looking at the current warehouse-backed range, which values are normal noise, which deserve attention, and which require immediate response?"

Listen for:

- `healthy_range`, `warning_threshold`, and `critical_threshold`.
- The time grain those thresholds apply to: hourly, daily, weekly, monthly, trailing window.
- Disagreements between historical percentiles and expert judgment.

Question: "Which business calendar events, customer cycles, launches, or operational seasons change the expected range, and by how much?"

Listen for:

- `seasonality` with magnitude and mechanism.
- Temporary threshold shifts, not just "holiday season" or "end of quarter."
- Event windows that should not be treated as anomalies.

Question: "Which segments need their own expectations instead of sharing the global threshold?"

Listen for:

- `segment_expectations` for customer tier, region, product line, processor, marketplace, plan, or channel.
- Contractual or operational reasons a segment's threshold differs.
- Segments where low volume makes thresholds unreliable.

Question: "When were these thresholds last calibrated, and what has changed since then?"

Listen for:

- `baseline_date` and evidence for recalibration.
- `trend` caused by product, pipeline, policy, traffic mix, or vendor changes.
- Stale assumptions that should block updating `last_validated`.

## Layer 3: Investigation

Question: "When this metric moves, what are the first three cuts you check, in order?"

Listen for:

- `causal_dimensions` with explicit priority order.
- Why each dimension is causal rather than merely convenient.
- Dimensions that are available in dbt/MetricFlow versus dimensions that require another tool.

Question: "What observation makes you switch from one hypothesis to another?"

Listen for:

- `investigation_path` as IF/THEN logic.
- Branch points based on magnitude, duration, segment concentration, freshness, or companion metrics.
- Stop conditions: when to stop investigating and escalate.

Question: "What apparent incidents are usually not real business problems?"

Listen for:

- `common_false_positives`.
- `data_quality_gotchas`: pipeline lag, backfills, delayed events, duplicate records, timezone changes, or schema changes.
- Checks that distinguish a real movement from a measurement artifact.

Question: "Which past incident changed how you investigate this metric?"

Listen for:

- `known_root_causes` with date, description, root cause, and resolution.
- Repeated failure modes.
- Missing runbook links or postmortems that should become source evidence.

## Layer 4: Relationships

Question: "What usually moves before this metric moves, and what lag should we expect?"

Listen for:

- `correlates_with` relationships with direction, magnitude, and lag.
- Leading indicators versus same-time companion metrics.
- Cases where correlation is seasonal or segment-specific.

Question: "What downstream metric, dashboard, SLA, or operating process changes when this metric changes?"

Listen for:

- `leads_to` relationships and expected lag.
- Dashboards or business reviews that depend on the metric.
- Downstream decisions that may also feed Layer 5.

Question: "What external events can move this metric even when the product or pipeline is healthy?"

Listen for:

- `affected_by` events with magnitude and duration.
- Launches, vendor outages, holidays, regulatory changes, pricing changes, traffic mix, or customer migrations.
- Events that should become explicit false-positive or seasonality notes.

Question: "When comparing this to related metrics, which dimensions must line up?"

Listen for:

- `shared_dimensions` that make cross-metric investigation possible.
- Grain mismatches that can cause incorrect joins or comparisons.
- Metrics that look related but should not be compared.

## Layer 5: Decisions

Question: "At each threshold, what exact action happens, who owns it, and what evidence do they need?"

Listen for:

- `when_this_drops` and `when_this_spikes` with concrete actions.
- `escalation_path` by severity.
- Evidence requirements before paging, notifying customers, or changing operations.

Question: "Which SLA, contract, regulatory rule, or internal policy changes the answer even when the metric appears healthy?"

Listen for:

- `business_rules`.
- Customer-tier or geography-specific obligations.
- Rules owned outside analytics: legal, finance, compliance, account management, or operations.

Question: "Where should alerts or updates go, and who is allowed to make the call?"

Listen for:

- `notification_channels`.
- Approval gates before public or customer-facing communication.
- Contacts that are roles or rotations, not brittle individual names.

Question: "How often should this card be re-reviewed, and what events force an earlier review?"

Listen for:

- `review_cadence`.
- Triggers for refreshing `last_validated`: contract renewal, vendor migration, dbt model change, new segment, incident, or threshold recalibration.
- Cases where partial updates should not advance `last_validated`.

## Closeout

End the interview by reading back the fields that changed:

- New values captured.
- Fields still missing and who owns them.
- Fields that need warehouse verification.
- Fields that require non-analyst approval, especially `business_rules`.

Do not treat the card as validated until the owner has reviewed the final YAML and Layer 2 thresholds have been checked against data.
