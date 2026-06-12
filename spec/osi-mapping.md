# OSI `ai_context` Mapping

How the Meta Context Schema's 36 fields map onto the [Open Semantic Interchange](https://github.com/open-semantic-interchange/OSI) `ai_context` field — and where they have no OSI home yet.

**OSI version referenced:** 0.1.1 (2025-12-11); checked against 0.2.0.dev0, which does not change `ai_context`.
**Posture:** This is an input to OSI, not a fork. The schema is a candidate answer to "what else belongs in `ai_context`?" If OSI adopts richer context fields, this repo's validator, distillation prompt, and agent skill retarget to them.

## What OSI defines today

`ai_context` attaches at five levels (semantic model, dataset, relationship, field, metric) as a string or an object with three recommended keys:

| OSI key | Type | Purpose |
|---------|------|---------|
| `instructions` | string | How AI should use this entity |
| `synonyms` | array | Alternative names and terms |
| `examples` | array | Sample questions / use cases |

OSI also defines `custom_extensions` (`vendor_name` + opaque JSON `data`) for vendor-specific payloads.

## Layer-by-layer mapping

| Meta Context layer | Representative fields | OSI home today | Fidelity |
|--------------------|----------------------|----------------|----------|
| 1. Context | `purpose`, `business_question`, `definition`, `owner`, `stakeholders` | `instructions` (prose) | Lossy — discrete fields collapse into one string; `owner`/`stakeholders` have no slot |
| 1. Context | `aliases` | `synonyms` | **Direct** — the one clean mapping |
| 2. Expectations | `healthy_range`, `warning_threshold`, `critical_threshold`, `seasonality`, `trend`, `target` | None | No home — numeric calibration data doesn't fit prose `instructions` without losing machine-readability |
| 3. Investigation | `causal_dimensions`, `investigation_path`, `common_false_positives`, `known_root_causes`, `data_quality_gotchas` | None | No home — conditional logic and incident history have no structured slot |
| 4. Relationships | `correlates_with`, `affected_by`, `leads_to`, `decomposes_into` | None | No home — OSI `relationships` are join topology (FK constraints), not semantic metric-to-metric relationships with direction/magnitude/lag |
| 5. Decisions | `when_this_drops`, `when_this_spikes`, `business_rules`, `escalation_path` | None | No home — SLAs and action protocols are absent from the spec |
| Cross-cutting | `last_validated`, `schema_version`, `review_cadence` | None | No home — no staleness or governance metadata in `ai_context` |

Summary: of the 36 fields, **one** maps directly (`aliases` → `synonyms`), roughly five collapse lossily into `instructions`, and the remaining thirty — the layers the [eval](../eval/results.md) shows close the calibration, framing, reasoning, and false-confidence failures — have no OSI home.

## Transport options until OSI extends `ai_context`

1. **dbt `meta:` blocks** (this repo's approach) — colocated with the metric, returned by the dbt Semantic Layer API, version-controlled. Works today; dbt-specific.
2. **OSI `custom_extensions`** — the full `meta:` payload can travel as `{vendor_name: "META_CONTEXT", data: "<json>"}` on any OSI entity. Interchange-safe but opaque: consumers must know the schema to read it. A worked example belongs here once someone needs it — open an issue.

## What we're proposing upstream

That OSI consider structured slots in `ai_context` (or a sibling key) for: expectations (ranges/thresholds with time grain), investigation guidance, semantic metric relationships, and decision rules — i.e., the field classes above with eval evidence behind them. Tracking: see the OSI discussion issue linked from the README once filed.
