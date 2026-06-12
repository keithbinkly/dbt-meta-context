# Sourcing Guide

Where to find the value for each schema field.

## Sourcing methods

| Method | Time | Best for |
|--------|------|----------|
| **Domain expert interview** | 30–60 min | investigation_path, causal_dimensions, business_rules, seasonality reasoning |
| **Historical data analysis** | 1–2 hrs | healthy_range, trend, correlates_with |
| **Operational documentation** | 15–30 min | business_rules, thresholds, escalation_path |
| **Query log mining** | 2–4 hrs | causal_dimensions priority ordering (most common GROUP BY patterns) |
| **Organizational memory** | Variable | affected_by events, known_root_causes |
| **Automated inference** | 1–2 hrs | correlates_with pairs and relationship types |

## Recommended sequence

Start with the cheapest, highest-yield sources. Do the metric and warehouse preflight first so interviews are grounded in actual distributions rather than memory alone:

0. **Metric and warehouse preflight** (15–30 min) — Confirm the metric compiles, inspect the semantic model grain, and run a quick trailing-window profile before asking humans to calibrate it. Fills or checks: `granularity`, `healthy_range`, `volatility`, `trend`, obvious segment differences, and whether the metric has enough history for reliable thresholds.

1. **Documentation extraction** (30 min) — Pull from existing runbooks, wikis, contracts. Fills: `business_rules`, `owner`, `purpose`, `aliases`, `thresholds`. Run the [distillation prompt](distillation-prompt.md) against whatever docs exist.

2. **Historical data analysis** (1 hr) — P5/P95, correlations, trend. Fills: `healthy_range`, `trend`, `correlates_with`, `seasonality` magnitude.

3. **Senior analyst interview** (1 hr) — The highest-value hour. Fills: `investigation_path`, `causal_dimensions`, `common_false_positives`, `known_root_causes`.

4. **Cross-team coordination** (variable) — For relationships and escalation. Fills: `affected_by`, `leads_to`, `escalation_path`, `segment_expectations`.

---

## Build a source coverage map before extraction

Before extracting context cards for multiple metrics, map source coverage by metric and layer. This is a lightweight checkpoint: it tells you which cards are ready for LLM distillation, which need interviews, and which carry false-confidence risk if authored from the current source packet.

| Metric | Layer | Fields needed | Available source document(s) | Freshness | Owner to interview | Gap or conflict | Risk | Next action |
|--------|-------|---------------|------------------------------|-----------|--------------------|-----------------|------|-------------|
| `order_success_rate` | L1 Context | `purpose`, `business_question`, `owner`, `definition` | Product wiki, data dictionary | Wiki current | Payments Analytics | `aliases` absent | Low: mostly naming risk | Ask 3 stakeholders for aliases |
| `order_success_rate` | L2 Expectations | `healthy_range`, `warning_threshold`, `critical_threshold`, `seasonality` | Incident runbook, warehouse history | Runbook 7 months old | Payments on-call | Thresholds conflict with dashboard annotation | Medium: stale or conflicting calibration | Verify thresholds against owner and trailing 12-month data |
| `order_success_rate` | L3 Investigation | `causal_dimensions`, `investigation_path` | On-call runbook | Current | Senior payments analyst | No false-positive examples | Medium: shallow triage guidance | Interview analyst before finalizing |
| `order_success_rate` | L4 Relationships | `correlates_with`, `affected_by` | QBR deck, incident reviews | Mixed | Payments Analytics | Lag and magnitude missing | Medium: weak reasoning about adjacent metrics | Add correlation query or owner note |
| `order_success_rate` | L5 Decisions | `when_this_drops`, `business_rules`, `escalation_path` | None found | N/A | Legal, account management, incident commander | No SLA or contract source | High: Layer 5 has no source → false-confidence risk | Do not use for obligation questions until sourced |

Use one row per metric-layer pair. For a batch of N metrics, sort high-risk rows first and resolve those before running the distillation prompt. A metric can proceed with partial extraction only if the coverage map makes the missing layers explicit and the downstream users know what questions the card is not safe to answer. For metrics tied to SLAs, contracts, regulated reporting, or customer obligations, do not treat Layer 2 thresholds as decision guidance unless Layer 5 `business_rules` has a current source.

---

## Field-by-field sourcing

### Layer 1: Context

| Field | Primary source | Secondary source |
|-------|---------------|-----------------|
| `purpose` | Metric owner interview | Existing documentation, wiki |
| `business_question` | Stakeholder interview: "What decision does this metric inform?" | Dashboard titles, report headers |
| `owner` | Org chart, on-call rotation | Data catalog |
| `stakeholders` | Metric owner: "Who asks you about this?" | Slack channel members |
| `definition` | Finance/accounting for financial metrics; legal for compliance | Data dictionary |
| `aliases` | Ask 3 different stakeholders what they call it | Search Slack for the metric name |
| `data_domain` | Obvious from context | Data catalog classification |
| `granularity` | dbt model grain documentation | Metric YAML type_params |

### Layer 2: Expectations

| Field | Primary source | Secondary source |
|-------|---------------|-----------------|
| `healthy_range` | P5/P95 from trailing 12 months data | Metric owner gut check |
| `warning_threshold` | Metric owner: "When do you start worrying?" | P10 from historical data |
| `critical_threshold` | Incident runbook, PagerDuty thresholds | Metric owner: "When do you page someone?" |
| `seasonality` | Historical data + metric owner explanation of WHY | Business calendar, major event log |
| `trend` | Time series analysis + metric owner context | QBR presentations |
| `target` | OKR/KPI documents | Leadership communications |
| `segment_expectations` | Contracts, SLA documents per customer tier | Account management team |
| `volatility` | Standard deviation from rolling 30-day window | Metric owner: "What's normal noise?" |
| `baseline_date` | Record when you calibrate | Calendar reminder to recalibrate |

### Layer 3: Investigation

| Field | Primary source | Secondary source |
|-------|---------------|-----------------|
| `causal_dimensions` | Senior analyst interview: "What do you check first?" | Query log mining (most frequent GROUP BY) |
| `investigation_path` | Senior analyst walkthrough of their decision tree | Post-incident review docs |
| `common_false_positives` | Senior analyst: "What trips up new analysts?" | Incident false-alarm history |
| `known_root_causes` | Post-incident reviews (last 12 months) | Slack #incidents archaeology |
| `data_quality_gotchas` | Data engineering team, pipeline monitoring | Known data delays, SLA documents |

### Layer 4: Relationships

| Field | Primary source | Secondary source |
|-------|---------------|-----------------|
| `correlates_with` | Statistical correlation analysis | Analyst intuition + confirmation |
| `affected_by` | Major events log, organizational memory | News monitoring for external factors |
| `leads_to` | Business process documentation | Analyst: "What downstream metric does this feed?" |
| `decomposes_into` | Metric definition: what sub-metrics compose this | dbt model lineage |
| `shared_dimensions` | dbt model inspection | Analyst: "I always join these two on..." |

### Layer 5: Decisions

| Field | Primary source | Secondary source |
|-------|---------------|-----------------|
| `when_this_drops` | Incident runbook, escalation playbook | Senior analyst: "What do you do when X drops?" |
| `business_rules` | Contracts, SLAs, regulatory docs | Legal/compliance team, account management |
| `when_this_spikes` | Incident runbook for upward anomalies | Data engineering: "What could cause a false spike?" |
| `escalation_path` | On-call rotation docs | Metric owner: "Who do you call when..." |
| `notification_channels` | PagerDuty, Slack, OpsGenie configuration | Incident response playbook |
| `review_cadence` | Team standup schedule, QBR calendar | Metric owner |

---

## Which layers need warehouse access

Only two layers require querying your data warehouse:

| Layer | What you're querying | Typical query |
|-------|---------------------|---------------|
| Layer 2 | Historical metric values | `SELECT PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY metric_value), PERCENTILE_CONT(0.95) ... FROM daily_metrics WHERE date >= CURRENT_DATE - 365` |
| Layer 4 (correlates_with) | Cross-metric correlations | Pearson correlation between metric pairs over trailing 12 months |

Everything else in the schema comes from documentation, interviews, and organizational memory — no warehouse access required.

### Layer 2 preflight checks

Before accepting `healthy_range`, `warning_threshold`, or `critical_threshold`:

- Confirm the metric's time grain and date spine.
- Pull trailing 12-month P5/P50/P95 and min/max at the intended grain.
- Check latest complete period and typical lag.
- Compare global values against important segments such as region, customer tier, processor, product line, or channel.
- Identify obvious one-off incidents before treating outliers as normal operating range.
- Record the query or dashboard used as threshold evidence.

The analyst interview should explain the ranges; it should not be the only evidence for them.
