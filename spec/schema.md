# Meta Context Schema Reference

**Schema version: 0.1.1** ([semver](https://semver.org/); version history in [CHANGELOG.md](../CHANGELOG.md) — the Core key set is declared stable).

Complete field inventory: 36 fields across 5 layers + cross-cutting metadata.

## Tier definitions

| Tier | Meaning | Time |
|------|---------|------|
| **Core** | Minimum viable. Each field addresses a failure mode demonstrated in ablation eval. | Bronze (~45 min/metric) |
| **Recommended** | Significant analytical value. Adds historical knowledge and downstream tracking. | Silver (~90 min/metric) |
| **Optional** | Useful but situational. Full organizational memory encoding. | Gold (~2 hrs/metric) |

## Placement: where context attaches

Context attaches to the thing it describes, at three levels: the **semantic model** (shared across all metrics on that model), the **metric** (specific to one measurement), and the **dimension** (vocabulary for one attribute). Metric-level values override model-level values — the validator implements this merge.

**Rule of thumb:** If the value would differ between metrics on the same model, it belongs at the metric level. If it would be redundant to repeat, it belongs at the model level. If it describes an attribute rather than a measurement, it belongs on the dimension.

### Model-level fields (shared)

| Field | Why shared |
|-------|-----------|
| `owner` | Same team owns all metrics on the model |
| `data_source` | Same underlying table/pipeline |
| `granularity` | Same model grain |
| `known_limitations` | Model-level quirks affect all metrics |
| `causal_dimensions` | Same dimensions available across the model |
| `affected_by` | Same external events hit all metrics |
| `escalation_path` | Usually same team/process |
| `last_validated` | Often validated together |

### Metric-level fields (specific per metric)

| Field | Why metric-specific |
|-------|-------------------|
| `purpose`, `business_question` | Count ≠ amount ≠ rate |
| `healthy_range`, `warning_threshold`, `critical_threshold` | Ranges are per-metric by definition |
| `investigation_path` | Different metrics break differently |
| `correlates_with` | Typed edges are metric-specific |
| `when_this_drops`, `when_this_spikes` | Actions diverge per metric |
| `business_rules` | SLAs and policies are metric-specific |

### YAML placement

```yaml
models:
  - name: my_daily_metrics
    semantic_model:
      meta:                        # ← model-level (shared)
        context:
          owner: "Analytics Team"
        investigation:
          causal_dimensions:
            - name: region
              why: "Primary segmentation"
              priority: 1
      metrics:
        - name: my_success_rate
          meta:                    # ← metric-level (specific)
            context:
              purpose: "Share of transactions completing successfully"
            expectations:
              healthy_range: [0.94, 0.99]
              warning_threshold: 0.92
            decisions:
              when_this_drops:
                - threshold: 0.92
                  action: "Check region breakdown first"
```

### Dimension-level: glossary cards

The full 36-field card is metric-shaped — a dimension has no healthy range or escalation path. What a dimension needs is a small **glossary card**: the vocabulary an agent must resolve before it can even pick the right filter. Attach it via the dimension's `config.meta` (dbt's `SemanticLayerElementConfig`):

```yaml
      dimensions:
        - name: payment_channel
          type: categorical
          config:
            meta:
              context:
                definition: "Business-friendly rollup of raw payment rail codes"
                aliases: ["channel", "payout method", "rail"]
                value_aliases:            # raw value → the names humans actually use
                  "card_push": "aka push-to-card, OCT (Original Credit Transaction)"
                  "rtp": "aka instant bank transfer, real-time payments"
                gotchas: "Values before 2024-03 use legacy upstream codes"
```

`value_aliases` is the load-bearing field: mapping raw codes to the names stakeholders actually say (the rail's nickname, the partner's brand name) is the single most common agent failure a dimension can prevent. Putting the glossary on the dimension — instead of repeating it inside every metric card that slices by it — means one source of truth that every metric inherits.

**Verification status (2026-06-12):** dimension `config.meta` parses under dbt Fusion and lands intact in `target/semantic_manifest.json` (the artifact the Semantic Layer serves), and the Semantic Layer API's dimension responses carry a per-dimension `metadata` field populated from `config.meta`. Until your manifest is refreshed with dimension meta, the pragmatic fallback is encoding vocabulary in the dimension `description`, which all APIs surface today.

This mirrors OSI's design: `ai_context` attaches at five levels (semantic model, dataset, relationship, field, metric), with `synonyms` as a field-level concern — see [`osi-mapping.md`](osi-mapping.md).

---

## Layer 1: Context — "Who cares and why does this exist?"

Closes: interpretation failures — the model describes the SQL formula instead of the business meaning.

| Key | Type | Tier | Description |
|-----|------|------|-------------|
| `purpose` | string | **Core** | What this metric measures and why. Scope-bounded: "from X through Y." Not "Revenue" — "Authorized transaction volume from auth request through settlement confirmation." |
| `business_question` | string | **Core** | The decision question this metric answers. "Is our payment processing performing normally?" |
| `owner` | string | **Core** | Primary team or role responsible. |
| `stakeholders` | list[string] | Recommended | Other teams who consume or are affected. |
| `definition` | string | Recommended | Precise business definition distinguishing from similar metrics. Especially useful when multiple metrics share a name across teams. |
| `aliases` | list[string] | Optional | Other names this metric goes by in the org. |
| `data_domain` | string | Optional | Business domain (e.g., "payments", "fulfillment", "finance"). |
| `granularity` | string | Optional | Grain the metric is computed at (daily, per-order, per-customer, etc.). |

---

## Layer 2: Expectations — "What does good look like?"

Closes: calibration failures — the model can't tell you if a number is concerning because it doesn't know what normal is.

| Key | Type | Tier | Description |
|-----|------|------|-------------|
| `healthy_range` | [number, number] | **Core** | P5/P95 operating range from trailing 12 months. |
| `warning_threshold` | number | **Core** | Value warranting attention but not yet critical. |
| `critical_threshold` | number | **Core** | Emergency value requiring immediate action. |
| `seasonality` | string | **Core** | When, how much, and why. Must include magnitude: "Drops 3-5pp in Nov-Dec due to post-holiday returns." Not "Yes." |
| `trend` | string | Recommended | Current direction and cause. "Gradually improving since Q3 processor upgrade." |
| `target` | number | Recommended | Aspirational goal. Distinct from healthy_range — this is what you're working toward. |
| `segment_expectations` | list[object] | Optional | Different thresholds per segment. `{segment, healthy_range, warning_threshold}` |
| `volatility` | string | Optional | Normal day-to-day variance — helps distinguish signal from noise. |
| `baseline_date` | string | Optional | When thresholds were last calibrated. Prevents stale ranges from misleading. |

---

## Layer 3: Investigation — "When it breaks, where do I look first?"

Closes: framing failures — the model lists all dimensions as equally valid instead of giving a prioritized decision tree.

| Key | Type | Tier | Description |
|-----|------|------|-------------|
| `causal_dimensions` | list[object] | **Core** | Dimensions to slice by, in priority order. Each: `{name, why, priority}`. |
| `investigation_path` | string | **Core** | Conditional decision tree, not a flat list. "IF drop > 3pp: check processor. IF processor-specific: check region within processor." |
| `common_false_positives` | list[string] | Recommended | Known scenarios that look like problems but aren't. |
| `known_root_causes` | list[object] | Recommended | Historical incidents: `{date, description, root_cause, resolution}`. |
| `data_quality_gotchas` | list[string] | Optional | Upstream data issues that mimic real drops. |

---

## Layer 4: Relationships — "What else moves when this moves?"

Closes: reasoning failures — the model treats the metric in isolation instead of reasoning about the system.

| Key | Type | Tier | Description |
|-----|------|------|-------------|
| `correlates_with` | list[object] | **Core** | Each: `{metric, relationship}`. Relationship must be specific — "inverse", "leading indicator — moves 15 min before", "upstream cause", not just "related". |
| `affected_by` | list[object] | **Core** | External events: `{event, impact}`. Include magnitude: "Major carrier outages can drop success rate 5-8pp for 2-4 hours." |
| `leads_to` | list[object] | Recommended | Downstream metrics this feeds. Directional: `{metric, lag}`. |
| `decomposes_into` | list[object] | Optional | Sub-metrics that compose to this one. |
| `shared_dimensions` | list[string] | Optional | Dimensions shared with correlated metrics — helps the model reason about joint breakdowns. |

---

## Layer 5: Decisions — "What do I do about it?"

Closes: action failures and false confidence. **Without this layer, Layers 2–4 create a dangerous middle state: the model is calibrated but lacks the rules needed to give correct action guidance. It will confidently anchor to healthy_range when answering SLA questions.**

| Key | Type | Tier | Description |
|-----|------|------|-------------|
| `when_this_drops` | list[object] | **Core** | Action protocols: `{threshold, action}`. Concrete and specific. |
| `business_rules` | list[string] | **Core** | SLAs, regulatory requirements, internal policies. The model cannot answer "are we meeting our obligations?" without this. |
| `when_this_spikes` | list[object] | Recommended | Action protocols for upward anomalies. |
| `escalation_path` | list[object] | Recommended | Who to escalate to: `{severity, contact, requires}`. |
| `notification_channels` | list[object] | Optional | Where alerts go: `{severity, channel}`. |
| `review_cadence` | string | Optional | How often formally reviewed. |

---

## Cross-cutting metadata

| Key | Type | Tier | Description |
|-----|------|------|-------------|
| `last_validated` | string (date) | Recommended | When this meta block was last reviewed. Flag as stale after 90 days. |
| `context_authored_by` | string | Optional | Who authored or last reviewed. |
| `schema_version` | string | Optional | Schema version, for migration tooling. |

---

## Summary

| Layer | Core | Recommended | Optional | Total |
|-------|------|-------------|----------|-------|
| 1. Context | 3 | 2 | 3 | **8** |
| 2. Expectations | 4 | 2 | 3 | **9** |
| 3. Investigation | 2 | 2 | 1 | **5** |
| 4. Relationships | 2 | 1 | 2 | **5** |
| 5. Decisions | 2 | 2 | 2 | **6** |
| Cross-cutting | — | 1 | 2 | **3** |
| **Total** | **13** | **10** | **13** | **36** |
