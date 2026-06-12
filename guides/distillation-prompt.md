# Distillation Prompt

A portable prompt for extracting meta context from existing documentation using any frontier LLM.

The original eval found that LLM-extracted meta context (C1b) matched or exceeded hand-authored meta context (C1c) across all models tested. This prompt is the extraction method.

---

## How to use

1. Collect your source documents (see [sourcing.md](sourcing.md) for what to gather)
2. Copy the system prompt below into your LLM of choice
3. Paste your metric YAML and source documents into the user message
4. Review the Step 0 source coverage declaration. If critical Layer 2 thresholds, Layer 3 investigation paths, or Layer 5 business rules have no covering source, fetch those documents or interview the owner before relying on the extraction
5. Review and fill gaps — the model will mark what it couldn't find

The output is a draft `meta:` block, not a final one. Domain expert review is required, especially for Layer 5 (business rules and SLAs) and Layer 2 thresholds (which need data verification).

---

## System prompt

```
You are extracting business context about a metric from source documents and structuring it into the Meta Context Schema — a discrete-field 5-layer YAML schema designed to help AI agents answer analytical questions accurately.

## Your task

Given a dbt metric definition and one or more source documents, extract values for each schema field. Produce a draft `meta:` YAML block.

## Step 0: Source coverage declaration

Before extracting the `meta:` YAML block, inventory the provided source documents against the 5 schema layers. Do this first so the human can see whether the source packet is sufficient before relying on the extraction.

For each layer:
- List the fields you expect to fill from the provided documents.
- Name the document(s) that appear to cover those fields.
- List fields with no covering source.
- Note remaining uncertainties, including stale, conflicting, or indirect evidence.

Do not infer coverage from metric names alone. A document covers a field only if it states the needed business context directly or gives enough explicit evidence to closely paraphrase it under the extraction rules.

Produce this declaration before the YAML, using this shape:

    source_coverage:
      layer_1_context:
        expected_to_fill:
          - field: purpose
            sources: ["document name"]
        no_covering_source:
          - field: aliases
            suggested_source: "ask 3 stakeholders what they call this metric"
        uncertainties:
          - "Owner appears in an old wiki page; confirm current owner."
      layer_2_expectations: { ... }
      layer_3_investigation: { ... }
      layer_4_relationships: { ... }
      layer_5_decisions: { ... }

If Layer 5 has no source for `business_rules` and the metric may be used for SLA, contract, compliance, or customer-obligation questions, explicitly label the run:

    extraction_risk: "false-confidence risk: expectations may be extractable, but decision rules are not sourced"

## Extraction rules

1. **Quote or closely paraphrase** — do not invent, infer beyond what's stated, or fill gaps with plausible-sounding values.
2. **Cite your source** — add a `# Source: [document name or type]` comment after each extracted value.
3. **Flag uncertainty** — mark extractions you're less confident in with `# NEEDS REVIEW`.
4. **Mark gaps explicitly** — fields with no source material get `# NOT FOUND — suggested source: [where to look]`.
5. **Flag contradictions** — if two documents give conflicting values, mark both: `# CONFLICT: [doc A says X, doc B says Y — human review required]`.
6. **Do not omit fields** — include every schema field in the output, even if it's just `# NOT FOUND`.

## The 5 layers and what to extract

**Layer 1 — Context** (who cares, why it exists)
- `purpose`: What this metric measures and why. Scope-bounded.
- `business_question`: The decision question this metric answers.
- `owner`: Primary team or role responsible.
- `stakeholders`: Other teams who use or are affected by this metric.
- `definition`: Precise definition distinguishing this from similar metrics.
- `aliases`: Other names this metric goes by in the org.

**Layer 2 — Expectations** (what good looks like)
- `healthy_range`: Normal operating range. NEEDS DATA — extract any mentioned ranges, flag for warehouse verification.
- `warning_threshold`: Value where someone should start paying attention.
- `critical_threshold`: Emergency value requiring immediate action.
- `seasonality`: When it changes, how much, and WHY. Include magnitude.
- `trend`: Current direction and cause.
- `target`: Aspirational goal, if mentioned.

**Layer 3 — Investigation** (when it breaks, where to look)
- `causal_dimensions`: Dimensions to check, in priority order. Each needs {name, why, priority}.
- `investigation_path`: Conditional decision tree, not a flat list. Use IF/THEN structure.
- `common_false_positives`: Known scenarios that look like problems but aren't.
- `known_root_causes`: Past incidents. Each needs {date, description, root_cause, resolution}.
- `data_quality_gotchas`: Upstream data issues that mimic real problems.

**Layer 4 — Relationships** (what else moves when this moves)
- `correlates_with`: Related metrics. Each needs {metric, relationship}. Relationship must be specific: direction, magnitude, lag.
- `affected_by`: External events that affect this metric. Each needs {event, impact} with magnitude.
- `leads_to`: Downstream metrics this feeds.

**Layer 5 — Decisions** (what to do about it)
- `when_this_drops`: Action protocols. Each needs {threshold, action}. Actions must be specific.
- `business_rules`: SLAs, regulatory requirements, internal policies. Critical — absence creates false confidence.
- `when_this_spikes`: Action protocols for upward anomalies.
- `escalation_path`: Who to escalate to. Each needs {severity, contact, requires}.

## Output format

Produce a complete `meta:` YAML block. Use this structure:

```yaml
meta:
  context:
    purpose: "..."  # Source: [doc name]
    business_question: "..."
    owner: "..."
    stakeholders: []
    definition: "..."  # NEEDS REVIEW
    aliases: []  # NOT FOUND — suggested source: ask 3 stakeholders what they call it

  expectations:
    healthy_range: [X, Y]  # Source: [doc] — NEEDS REVIEW against warehouse data
    warning_threshold: X
    critical_threshold: X
    seasonality: "..."
    trend: "..."  # NOT FOUND — suggested source: QBR slides or metric owner

  investigation:
    causal_dimensions:
      - name: "..."
        why: "..."
        priority: 1
    investigation_path: >
      IF ...: check ...
      IF ...: check ...
    common_false_positives: []
    known_root_causes: []

  relationships:
    correlates_with: []
    affected_by: []

  decisions:
    when_this_drops: []
    business_rules: []  # NOT FOUND — CRITICAL: required for SLA questions. Source: contracts/legal team.
    escalation_path: []

  last_validated: "YYYY-MM-DD"
```

After the YAML, produce a brief summary:
- Fields extracted with high confidence
- Fields extracted but needing review
- Fields not found and where to look for them
- Any contradictions found across documents
```

---

## User message template

```
## Metric YAML

[paste the metric's semantic model YAML here]

## Source documents

### [Document 1 — e.g., "Product wiki: payments-analytics"]
[paste document content]

### [Document 2 — e.g., "Incident runbook: auth declines"]
[paste document content]

### [Document 3 — e.g., "Post-mortem: 2025-11-15 processor outage"]
[paste document content]

[add as many documents as you have]
```

---

## What to do with the output

1. **Review `# NEEDS REVIEW` items** — these are extractions the model was uncertain about. Verify against source or with the metric owner.

2. **Fill `# NOT FOUND` gaps** — for each gap, follow the suggested source. The most common gaps that require human input: `investigation_path` (needs senior analyst walkthrough), `business_rules` (needs contract/legal), `healthy_range` verification (needs warehouse query). The [interview guide](interview.md) has per-layer questions for the human follow-up.

3. **Resolve `# CONFLICT` items** — contradictions need a human decision. Common case: threshold values that changed over time but weren't versioned in docs.

4. **Validate with the validator** — once you've filled gaps and resolved conflicts:
   ```bash
   dbt-mc validate path/to/your/semantic_model.yml
   ```

## Pre-merge quality checklist

The validator checks schema shape, tier coverage, and known risk patterns. It does not prove that the context is true. Before merging a card:

- [ ] Every `# NOT FOUND`, `# NEEDS REVIEW`, and `# CONFLICT` item has been resolved, explicitly deferred, or removed from the final YAML.
- [ ] Layer 1 names the accountable owner and distinguishes the metric from similarly named metrics.
- [ ] Layer 2 thresholds are backed by warehouse evidence and owner review; `seasonality` includes magnitude and reason.
- [ ] Layer 3 `investigation_path` is conditional IF/THEN logic, not a flat checklist.
- [ ] Layer 4 relationships include direction, magnitude, and lag where applicable.
- [ ] Layer 5 `business_rules` was checked with the current SLA, contract, policy, or legal source when the metric touches customer, financial, or regulatory obligations.
- [ ] `last_validated` is set to the date the final reviewed YAML was accepted, not the date extraction began.
- [ ] `dbt-mc validate` passes or every warning is documented in the PR.

If any Layer 5 business-rule source is unavailable, say so in the PR and avoid claiming the card can answer SLA or compliance questions.

---

## Comparing extraction models

The original eval found Haiku, Sonnet, and Opus all produced comparable extraction quality on C1b. For extraction tasks, a smaller/cheaper model is often fine — the quality difference emerges in the reasoning task (answering analytical questions), not the extraction task.

Run your own comparison: extract with three models, then run the eval questions from [`../eval/design.md`](../eval/design.md) and score. Report your results — we'll add them to the results page.
