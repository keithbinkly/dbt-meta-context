# dbt-meta-context

**Context cards for dbt metrics.** Encode business knowledge — thresholds, investigation paths, SLAs, metric relationships — directly in dbt MetricFlow YAML, so AI agents answer analytical questions accurately instead of confidently wrong.

[![skills.sh](https://skills.sh/b/keithbinkly/dbt-meta-context)](https://skills.sh/keithbinkly/dbt-meta-context) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Using an agent?** Ask Claude Code, Codex, or Cursor to install the authoring skill from your project directory:

```bash
npx skills add keithbinkly/dbt-meta-context --skill authoring-meta-context
```

The skill teaches your agent the full workflow: source the docs, distill them into a context card, fill gaps with the owner, validate.

**Validating cards in CI?** Install the CLI:

```bash
pip install "git+https://github.com/keithbinkly/dbt-meta-context.git#subdirectory=validator"
dbt-mc validate path/to/semantic_models.yml
```

## The problem

Your semantic layer has perfect metric definitions. But when you ask an AI agent "is our success rate concerning this week?" it gives you a generic, hedged non-answer — or worse, a confident wrong one. The metric definition tells the model *what* a metric is. It doesn't tell it *what good looks like*, *where to look when it breaks*, or *what to do about it*.

That knowledge exists in your org — in runbooks, post-mortems, analyst heads, SLA contracts. The schema gives each metric a **context card**: a structured home for everything the metric definition alone doesn't tell you.

## Relationship to existing standards

This complements the context standards now emerging — it does not compete with them:

- **OSI `ai_context`** (Open Semantic Interchange — dbt Labs, Snowflake, Salesforce et al.) defines `instructions`, `synonyms`, and `examples`. The right slot, with a thin payload. This schema is a candidate answer to "what else goes in that slot" — thresholds, investigation paths, business rules, metric relationships. Field-by-field mapping: [`spec/osi-mapping.md`](spec/osi-mapping.md).
- **dbt `meta:`** is the delivery mechanism, not a rival — the schema lives inside it, so nothing here requires changes to dbt.
- **Fivetran/dbt Agents Schema** delivers context as warehouse tables an agent can `SELECT`; see [`spec/prior-art.md`](spec/prior-art.md) for the comparison.
- **Execution layers like ktx** consume context to run queries; this repo covers the authoring and governance side — writing, validating, and maintaining the context such tools read.

## Why this approach

### Inference cost: pay once, read many times

Answering a question with a raw text-to-SQL agent carries three costs on every query:

1. **Query construction** — the model writes and validates SQL against your schema
2. **Data retrieval** — the warehouse runs the query
3. **Context reasoning** — the model searches scattered docs, runbooks, and tribal knowledge to interpret the result

The semantic layer eliminates cost 1: MetricFlow translates the metric call to SQL, so the model doesn't write queries. The context card eliminates cost 3: the reasoning about what healthy looks like, where to investigate, and what the business rules are is done **once at authoring time**, with a frontier model, and stored in the YAML. Every query after that reads the card. Reading a pre-structured card doesn't require frontier-level reasoning — a smaller, cheaper, faster model handles it correctly.

One-time frontier investment at build time → unlimited cheap queries at high-accuracy. That is what the eval table below measures.

### No new connector

The context card lives in the same YAML file the Semantic Layer API already reads. When your agent calls the dbt Semantic Layer for a metric, the `meta:` block is available in the same response — no new integration, no new authentication, no new vendor to wire up and maintain. The context is colocated with the metric definition by design.

### Version-controlled and point-in-time auditable

Because the card is a YAML block in your dbt project, it goes through PR review and has full git history. You can prove exactly what the system knew about a metric on any given date — what thresholds were in effect, what business rules applied, who reviewed and approved the change. For regulated industries, this is a requirement, not a nice-to-have.

## Key finding

**Haiku + meta context (4.7) outperforms Opus + scattered docs (4.6).**

One-time extraction of scattered documentation into the schema enables unlimited cheap queries at near-frontier-model quality. The model gap on bare schemas is 0.8 points. With meta context, it collapses to 0.2.

| Condition | Haiku | Sonnet | Opus |
|-----------|-------|--------|------|
| Bare schema (C0) | 2.3 | 2.7 | 3.1 |
| Meta context — extracted (C1b) | 4.7 | 4.8 | 4.9 |
| Meta context — hand-authored (C1c) | 4.6 | 4.8 | 4.9 |
| Clean docs, no meta (C2) | 3.8 | 4.1 | 4.5 |
| Full docs, no meta (C3) | 4.0 | 4.3 | 4.5 |

Scores on a 5-point rubric across 5 analytical failure types. See [`eval/results.md`](eval/results.md) for methodology and full results.

## The schema

36 fields across 5 layers, each closing a specific AI analytical failure type:

| Layer | Question it answers | Failure it closes |
|-------|--------------------|--------------------|
| 1. Context | Who cares and why does this exist? | Interpretation |
| 2. Expectations | What does good look like? | Calibration |
| 3. Investigation | When it breaks, where do I look first? | Framing |
| 4. Relationships | What else moves when this moves? | Reasoning |
| 5. Decisions | What do I do about it? | Action + false confidence |

**Critical finding:** Layers 2–4 without Layer 5 create false confidence. An agent that knows healthy ranges but not business rules will give confidently wrong answers on SLA and decision questions. Layer 5 is what separates a calibrated response from a calibrated-but-wrong one.

## Quick start

Add a `meta:` block to any metric in your semantic model YAML:

```yaml
metrics:
  - name: order_success_rate
    type: derived
    meta:
      context:
        purpose: "Share of transactions completing successfully, from auth through settlement"
        business_question: "Is our payment processing performing normally?"
        owner: "Payments Analytics"

      expectations:
        healthy_range: [0.94, 0.99]
        warning_threshold: 0.92
        critical_threshold: 0.89
        seasonality: "Drops 2-3pp in late November due to Black Friday carrier volume"

      investigation:
        causal_dimensions:
          - name: processor
            why: "Single processor failures account for 80% of drops"
            priority: 1
          - name: region
            why: "Regional outages are the second most common cause"
            priority: 2
        investigation_path: >
          IF drop > 3pp: check processor breakdown first.
          IF processor-specific: check region within processor.
          IF all processors affected: check upstream auth service.

      relationships:
        correlates_with:
          - metric: auth_approval_rate
            relationship: "leading indicator — auth rate moves 15-30 min before success rate"
        affected_by:
          - event: "Major carrier outages"
            impact: "Can drop 5-8pp for 2-4 hours"

      decisions:
        when_this_drops:
          - threshold: 0.92
            action: "Page payments-oncall. Check processor dashboard."
          - threshold: 0.89
            action: "Escalate to VP Payments. Consider partner notifications."
        business_rules:
          - "Enterprise SLA requires >0.95 monthly average. Breach triggers credit."
```

This exact card lives in [`examples/order_success_rate.yml`](examples/order_success_rate.yml) — clone the repo and try the validator on it: `dbt-mc validate examples/`.

That's Bronze tier — the 13 Core fields. Takes about 45 minutes per metric, mostly from existing runbooks and a conversation with the metric owner.

## Tiers

| Tier | Fields | Time | What you get |
|------|--------|------|--------------|
| Bronze | 13 Core fields | ~45 min/metric | Calibrated responses, basic investigation guidance |
| Silver | + 10 Recommended | ~90 min/metric | Historical knowledge, downstream tracking, false-positive detection |
| Gold | All 36 fields | ~2 hrs/metric | Full organizational memory, automated decision routing |

Start with your 5-10 most-questioned metrics. Bronze tier for those is more valuable than Gold tier for one.

## What's in this repo

| Path | What |
|------|------|
| [`spec/schema.md`](spec/schema.md) | Complete field reference — all 36 fields, types, examples, tiers |
| [`spec/field-guide.md`](spec/field-guide.md) | 4-test framework for proposing schema extensions |
| [`spec/prior-art.md`](spec/prior-art.md) | How this compares to other vendors' context layers |
| [`spec/known-gaps.md`](spec/known-gaps.md) | Known schema limitations and workarounds (multi-tenancy, versioning, temporal validity) |
| [`eval/design.md`](eval/design.md) | Ablation methodology — how to run your own eval |
| [`eval/results.md`](eval/results.md) | Full results from the original 6-condition experiment |
| [`eval/extraction-quality.md`](eval/extraction-quality.md) | How to evaluate the extraction step itself (coverage, citation fidelity, gap detection) |
| [`guides/authoring.md`](guides/authoring.md) | How to write effective context values — plus context budget, staleness, and maintenance |
| [`guides/sourcing.md`](guides/sourcing.md) | Where to find each field's data, warehouse preflight, source coverage map |
| [`guides/interview.md`](guides/interview.md) | Domain-expert interview questions for the fields documents rarely contain |
| [`guides/distillation-prompt.md`](guides/distillation-prompt.md) | Prompt for extracting meta context with any frontier LLM |
| [`skills/authoring-meta-context/`](skills/authoring-meta-context/) | Installable agent skill wrapping the authoring workflow |
| [`validator/`](validator/) | Python CLI for validating meta context blocks |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to propose schema extensions |

## Validator

```bash
pip install "git+https://github.com/keithbinkly/dbt-meta-context.git#subdirectory=validator"
dbt-mc validate path/to/semantic_models.yml
```

Reports tier (Bronze/Silver/Gold), missing fields, type errors, and false-confidence risk.

## Extraction

If you have existing runbooks, post-mortems, or onboarding docs, a frontier model can extract the schema from them directly. See [`guides/distillation-prompt.md`](guides/distillation-prompt.md).

## The agent skill

The install command at the top adds [`skills/authoring-meta-context/`](skills/authoring-meta-context/) to your agent, which then auto-loads the authoring workflow whenever you ask about context cards or meta context. The skill is a thin navigation layer over the guides in this repo — updating the guides updates the skill.

## Contributing

We welcome schema extensions. All proposed fields must pass the 4-test framework in [`spec/field-guide.md`](spec/field-guide.md) and be validated against an eval fixture. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT
