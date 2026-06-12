# Authoring Guide

How to write meta context — a populated `meta:` block is a metric's **context card** — that actually helps AI agents reason correctly.

## Five principles

### 1. Write for the worst-case consumer

Assume a new analyst or an LLM with no prior context. No jargon, no assumed knowledge, no org-specific abbreviations without expansion.

```yaml
# BAD — assumes the reader knows what SFP means
purpose: "SFP success rate by program"

# GOOD
purpose: >
  Share of Secure Funds Program transactions that complete successfully,
  from authorization through settlement. Excludes pending transactions.
```

### 2. Encode reasoning, not just facts

Facts tell you what happened. Reasoning tells you why — and why matters for investigation.

```yaml
# BAD — just a fact
seasonality: "Drops in December"

# GOOD — includes the mechanism
seasonality: >
  Drops 3-5pp in late November through December.
  Cause: post-holiday return season inflates the declined transaction count
  without affecting the authorization count, compressing the rate.
  Expect recovery by mid-January.
```

### 3. Use specific relationship types, not adjectives

Relationship descriptions should tell the model the direction, magnitude, and lag — not just that two things are "related."

```yaml
# BAD
correlates_with:
  - metric: auth_approval_rate
    relationship: "related"

# GOOD
correlates_with:
  - metric: auth_approval_rate
    relationship: "leading indicator — auth_approval_rate moves 15-30 min before success_rate during processor incidents"
  - metric: return_rate
    relationship: "inverse — high return_rate in subsequent weeks lags low success_rate by 5-7 days"
```

### 4. Include magnitude

Without magnitude, thresholds and seasonality provide no calibration value.

```yaml
# BAD — no magnitude
seasonality: "Drops during peak season"
warning_threshold: 0.92  # but what's normal?

# GOOD — magnitude included
healthy_range: [0.94, 0.99]
warning_threshold: 0.92
seasonality: "Drops 3-5pp during Black Friday week. Expected range shifts to [0.90, 0.97]."
```

### 5. Write investigation paths as conditional logic

A flat list of things to check is not an investigation path. A decision tree is.

```yaml
# BAD — flat list
investigation_path: "Check processor, region, and time of day"

# GOOD — conditional logic
investigation_path: >
  IF drop > 3pp: start with processor breakdown.
    IF single processor: check region within that processor.
    IF all processors: check upstream auth service health.
  IF drop < 1pp but persistent: check data pipeline freshness first.
  IF spike in specific hours: check batch job schedule conflicts.
```

---

## One decision regime per card (the tidy rule)

Tidy data gives each observational unit its own table. The card-level equivalent: **each decision regime gets its own metric, and therefore its own card.**

The dividing line runs between Layer 2 and Layer 5:

- **Layer 2 varying by segment is tolerable.** `segment_expectations` is a calibration lookup table — an agent can index into it mechanically:

  ```yaml
  expectations:
    segment_expectations:
      consumer:   { healthy_range: [0.92, 0.97] }
      commercial: { healthy_range: [0.96, 0.99] }
  ```

- **Layer 5 varying by segment is the split signal.** If `business_rules` or `when_this_drops` differ by segment value, you have two decision objects wearing one metric's name. An SLA is a contract about a *specific* population; modeling it as a CASE branch inside a blended metric's card means the agent must reconstruct the regime boundary at query time — exactly the inference the card exists to pre-pay.

The rule, stated tidily: **one card, one decision regime.** If you're writing conditional logic inside Layer 5, that's not a card problem — it's a semantic model problem. Split the metric. MetricFlow supports this directly with filtered metrics:

```yaml
metrics:
  - name: commercial_auth_rate
    type: simple
    type_params:
      measure: auth_approvals_rate_inputs
    filter: "{{ Dimension('transaction__card_tier') }} = 'commercial'"
    meta:
      expectations:
        healthy_range: [0.96, 0.99]      # one regime, one range
      decisions:
        business_rules:
          - "Commercial SLA requires >0.96 monthly average. Breach triggers credit."
        when_this_drops:
          - threshold: 0.96
            action: "Notify enterprise team via PagerDuty P2"
```

The per-regime metric carries one healthy range, one runbook, one SLA. The blended metric keeps a thin card whose Layer 5 says "decision regimes live on the per-segment metrics" and points to them via `decomposes_into`. Keep the blended metric for cross-segment comparison — just stop hanging contracts on it.

**Scope:** this is not a global modeling requirement — applied everywhere it causes metric proliferation. The conditional form is the rule: **populations bearing SLAs or decision triggers must be tidy; purely descriptive metrics may stay blended.** See [`../spec/known-gaps.md`](../spec/known-gaps.md) Gap 1 for the multi-tenant case this resolves and the fallback when the split doesn't scale.

---

## Anti-patterns

| Pattern | Why it fails |
|---------|-------------|
| `purpose: "Revenue"` | Too vague — which revenue? Which time window? What excludes? |
| `healthy_range: [0, 1]` | Technically correct, zero calibration value |
| `investigation_path: "Check the data"` | Not an investigation path — it's a non-instruction |
| `business_rules: ["Important metric"]` | Not a business rule — just an opinion |
| `correlates_with: [{metric: "return_rate"}]` | Missing relationship type — the model can't reason about direction or lag |
| `seasonality: "Yes"` | Boolean when a description with magnitude is needed |
| `when_this_drops: [{threshold: 0.5, action: "investigate"}]` | Threshold is too low to be useful; action is not specific |

---

## Context budget: how much is enough, how much is too much

Context cards make agents more accurate — but only up to a point. A practical rule of thumb from agent context engineering: model performance degrades when large volumes of non-task-specific context are loaded simultaneously. At query time, your agent typically receives:

- The user's question
- The metric definition (the MetricFlow YAML minus `meta:`)
- The context card itself

If your org has 50+ metrics and a query touches multiple cards, the combined payload can easily breach the effective attention budget. Structured cards compress well — but the compression is not unlimited. The original eval makes the point empirically: the full-docs condition (C3) scored 0.7 points *lower* than the extracted card (C1b) despite containing strictly more information.

### Per-card size budgets by tier

| Tier | Field count | Approximate token cost | Notes |
|------|------------|----------------------|-------|
| Bronze (Core) | 13 fields | ~200–400 tokens | Safe for any query context |
| Silver (+Recommended) | 23 fields | ~500–800 tokens | Fine for single-metric queries |
| Gold (all 36 fields) | 36 fields | ~900–1,400 tokens | Use selective retrieval for multi-metric queries |

*Token estimates assume verbose, well-written values. Terse values cost less.*

### Multi-metric query: selective retrieval guidance

When a query spans multiple metrics, do not load all layers for all metrics. Load selectively based on the question type:

| Question type | Load for all metrics | Load only for primary metric |
|--------------|---------------------|------------------------------|
| "Is X normal?" (calibration) | Layer 1 (Context) + Layer 2 (Expectations) | — |
| "Why is X dropping?" (investigation) | Layer 1 | Layers 3–4 |
| "What should we do about X?" (action) | Layer 1 | Layers 2–5 |
| "Are we meeting our SLA?" (compliance) | Layer 1 | Layer 5 only |

The pattern: broad context (who/why) for all cards; deep context (thresholds, paths, rules) only for the metric the question is actually about. See [`../spec/known-gaps.md`](../spec/known-gaps.md) Gap 4 for the open schema design work here.

### Long `investigation_path` and `known_root_causes`

These are the two fields most likely to balloon. Keep them bounded:

- `investigation_path`: Cap at ~150 words. Use conditional branching, not prose. If your investigation tree is longer than that, it likely needs to be split into multiple metrics or moved to a separate runbook that the card references by URL.
- `known_root_causes`: Limit to the 3–5 most recent or most frequent incidents. Archive older entries to a linked post-mortem doc; don't let them accumulate in YAML.

Treat ~150 words per prose field as a working ceiling when authoring.

---

## Trust levels and staleness: what an agent does with your card

A context card is **trusted content** — the agent treats it as authoritative, the way it treats source code or type definitions. That is what makes it effective. It is also what makes stale or incorrect cards dangerous. An agent that reads a card with an outdated `warning_threshold` will give a confidently wrong calibration answer.

### The `last_validated` field is load-bearing

`last_validated` is listed as Recommended, but it functions as a staleness gate: the validator warns on cards older than 90 days. Treat it as Core for any metric where an incorrect answer would matter — which is most of them.

What "validated" means:
- All threshold values still reflect the metric's current operating range
- All `business_rules` entries still reflect current contracts and policies
- The `investigation_path` still reflects how your team actually investigates

What "validated" does NOT require: re-running the full sourcing workflow, re-interviewing every stakeholder, or re-pulling historical data. A review session with the current metric owner is sufficient.

### Staleness risk by field

Some fields go stale faster than others:

| Field | Stale after | Why |
|-------|------------|-----|
| `warning_threshold`, `critical_threshold` | 6–12 months | Operating conditions shift; old thresholds create false alarms or missed alerts |
| `business_rules` | Contract renewal date | SLA terms change; stale rules cause compliance misclassification |
| `escalation_path` | On-call rotation changes | Pages the wrong person |
| `investigation_path` | Infrastructure changes | Points to components that no longer exist |
| `healthy_range` | 12 months | Seasonal drift; needs re-calibration annually |
| `purpose`, `owner`, `business_question` | Org restructuring only | Rarely stale |

### Prompt-injection surface

Context cards are org-authored YAML that will be fed to an LLM at query time. The risk of prompt injection through `meta:` blocks is low but non-zero — especially if your distillation pipeline ingests external documents (vendor runbooks, third-party SLA templates) and writes their prose directly into card fields.

Safe practice:

1. If your distillation source includes third-party content, review every `business_rules` and `investigation_path` value before committing. Look for instruction-like text: "ignore previous instructions", "you are now", URLs to external resources, shell commands.
2. The validator does not scan for injection patterns. Treat cards distilled from external sources as "verify before committing" — the same trust level you apply to third-party config files in code review.
3. Cards distilled from internal docs (runbooks you own, contracts you hold) are safe to treat as trusted on commit.

---

## Sourcing checklist before authoring

See [`sourcing.md`](sourcing.md) for the full sourcing workflow: the warehouse preflight, the source coverage map, and the field-by-field source table. With sources in hand, the [distillation prompt](distillation-prompt.md) fills 60–70% of the schema before any human authoring, and the [interview guide](interview.md) covers the rest.

---

## Layer-by-layer walkthrough

### Layer 1 (Context)

Start here. If you can't write a crisp `purpose` and `business_question`, the metric definition itself needs work before meta context will help.

Useful questions:
- "In one sentence, what decision does this metric inform?"
- "Who asks you about this metric, and what are they usually trying to figure out?"
- "What's the most common misconception about what this metric includes or excludes?"

### Layer 2 (Expectations)

Requires data access. Pull P5/P95 from trailing 12 months for `healthy_range`. Ask the metric owner "at what value do you start worrying?" for `warning_threshold`. Check incident runbooks for `critical_threshold`.

Don't skip `seasonality`. A model that knows "this drops 4pp in November" will not flag a 3pp November drop as an anomaly. A model without this context will.

### Layer 3 (Investigation)

The highest-value authoring hour. Talk to the senior analyst who owns this metric. Ask: "Walk me through exactly what you do when this drops." Their answer is your `investigation_path`.

Ask separately: "What's the most common false alarm you've seen with this metric?" → `common_false_positives`.

### Layer 4 (Relationships)

Two parts:
- Statistical: correlation analysis over 12 months for `correlates_with`
- Organizational: "what major events have affected this metric?" → `affected_by`

The statistical part can be automated. The organizational memory part requires a human.

### Layer 5 (Decisions)

Extract from contracts, SLA documents, and escalation playbooks. This layer requires cross-team access (legal, finance, account management) for financial metrics.

**Do not skip `business_rules` for any metric tied to a customer or regulatory SLA.** Without it, your schema is calibrated but will answer compliance questions incorrectly.

---

## Verification checklist

After authoring or updating a context card, confirm:

### Content quality
- [ ] Every prose field passes the "worst-case consumer" test — no unexpanded acronyms, no assumed org context
- [ ] `healthy_range` is drawn from at least 12 months of data, not a guess
- [ ] `seasonality` includes magnitude (a number, not "yes" or "sometimes")
- [ ] `investigation_path` is a conditional decision tree, not a flat list
- [ ] `correlates_with` specifies direction and lag, not just the other metric name
- [ ] `business_rules` covers every SLA or regulatory obligation on this metric
- [ ] No field contains the text "investigate", "check", or "review" without a specific next action attached

### Staleness and trust
- [ ] `last_validated` is set to today's date
- [ ] If the card was distilled from external sources, all `business_rules` and `investigation_path` values have been reviewed for instruction-like text
- [ ] `escalation_path` contacts are current (check against on-call rotation)
- [ ] Thresholds have been confirmed against current operating data, not copied from an older card or a neighboring metric

### Validator
- [ ] `dbt-mc validate` reports at least Bronze tier
- [ ] No false-confidence warnings (missing Layer 5 `business_rules` on a metric tied to SLAs)

### Size budget (for Gold-tier cards)
- [ ] No prose field exceeds ~150 words
- [ ] `known_root_causes` is limited to the 5 most recent or frequent incidents
- [ ] If this card will be loaded alongside 10+ other cards in multi-metric queries, selective retrieval guidance has been shared with the query author

---

## Maintaining cards

Treat a wrong agent answer as a context-card gap until proven otherwise. Do not patch around the failure with a one-off prompt. Load the current `meta:` block, identify which field would have prevented the wrong answer, update that field with evidence, then run validation again.

### Iteration workflow

1. Capture the failure: user question, metric, returned answer, expected answer, and why the answer was wrong.
2. Diagnose the missing or stale field using the table below.
3. Do targeted discovery only for that gap: warehouse query, domain-expert interview, runbook review, contract review, or incident review.
4. Update the smallest relevant field set. Avoid dumping the incident into a free-text note if a discrete field exists.
5. Run `dbt-mc validate`.
6. Update `last_validated` only after the metric owner or owning team has reviewed the changed card.

### Symptom-to-field diagnosis

| Agent failure symptom | Likely missing or stale fields |
|-----------------------|--------------------------------|
| Says a value is concerning when it is normal, or normal when it is concerning | `healthy_range`, `warning_threshold`, `critical_threshold`, `seasonality`, `volatility`, `baseline_date` |
| Uses global thresholds for a segment with different behavior | `segment_expectations`, `business_rules` |
| Gives a flat or wrong investigation plan | `causal_dimensions`, `investigation_path` |
| Misses a known false alarm or data artifact | `common_false_positives`, `data_quality_gotchas` |
| Ignores a past incident pattern | `known_root_causes`, `investigation_path` |
| Misstates which metrics move together or in what order | `correlates_with`, `leads_to`, `affected_by`, `shared_dimensions` |
| Gives confident but wrong SLA, contract, or escalation advice | `business_rules`, `when_this_drops`, `when_this_spikes`, `escalation_path`, `notification_channels` |
| Relies on thresholds or business rules that changed recently | `last_validated`, `baseline_date`, `review_cadence`, plus the stale field itself |

### Updating `last_validated`

`last_validated` means the card was reviewed, not merely edited. Advance it when:

- Layer 2 thresholds were checked against current data or explicitly re-approved by the owner.
- Layer 5 rules were checked against the current contract, SLA, regulatory, or policy source when applicable.
- The accountable owner reviewed the final YAML.

Do not advance it for partial drafts, unresolved `# NEEDS REVIEW` items, or isolated edits that have not been reviewed. If only one layer was validated, document that in the PR description and leave a follow-up issue for full-card review.

---

## Common rationalizations

Teams often resist authoring context cards. The objections and the honest responses:

| Rationalization | Reality |
|----------------|---------|
| "Our runbooks already have this. Why duplicate it?" | Runbooks are unstructured prose. The card's value is *structure* — a model that reads a card doesn't need to search, parse, or reconcile 7 documents. The distillation prompt copies the work over from the runbooks you already have. |
| "The model should figure it out from the metric name" | It can't. The eval shows bare schemas score 2.3/5. Your metric name is not a runbook. |
| "We'll add context cards after the semantic layer is stable" | Context cards are independent of MetricFlow stability. You can add `meta:` blocks before the semantic layer is in production. The cost of waiting is every agent interaction until you ship. |
| "We only have 2 or 3 metrics that really matter" | Then those 2 or 3 metrics are exactly where to start. Bronze tier on your top 5 is more valuable than Gold tier on one. |
| "Thresholds will be wrong and we'll have to update them" | The alternative is no thresholds — which means calibration failures on every query. Wrong thresholds are better than absent ones, and `last_validated` tells the model when to be skeptical. |
| "We don't have time to interview the senior analyst" | The distillation prompt fills 60–70% from existing docs with no interviews. The interview fills the gaps; it is not the starting point. |

---

## Red flags: your cards may need attention

- An agent answers a calibration question and doesn't cite any threshold — your `healthy_range` or `warning_threshold` may be absent or too vague to use
- An agent gives a hedged "it depends" answer on a decision question when your team has a clear escalation policy — `business_rules` or `when_this_drops` is likely missing
- The same question asked twice with slightly different wording gives opposite conclusions — the model is hallucinating in the gaps; find the specific missing field
- `last_validated` is absent or more than 90 days old and nothing is flagging it — your staleness gate is not wired into CI
- An agent cites a runbook URL or Confluence page from a `business_rules` field and the link is dead — your card is pointing to stale external sources
