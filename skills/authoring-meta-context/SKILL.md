---
name: authoring-meta-context
description: >
  Authors and extracts dbt MetricFlow meta context — structured YAML `meta:` blocks
  that encode business knowledge (thresholds, investigation paths, SLAs, relationships)
  alongside metric definitions so AI agents answer analytical questions accurately.
  Use when user asks about context cards, meta context blocks, dbt metric meta blocks,
  semantic layer context, distilling runbooks into YAML, authoring meta context,
  validating meta context, or improving AI agent analytical accuracy on dbt metrics.
---

# Authoring Meta Context

## Quick start

1. Gather source docs (runbooks, wikis, SLA contracts, post-mortems) for your target metric.
2. Run the distillation prompt against them: see [guides/distillation-prompt.md](https://github.com/keithbinkly/dbt-meta-context/blob/main/guides/distillation-prompt.md).
3. Paste the draft `meta:` block into your semantic model YAML.
4. Validate: `dbt-mc validate path/to/semantic_model.yml`
5. Fill `# NEEDS REVIEW` and `# NOT FOUND` gaps from the output.

**Start with Bronze tier (13 Core fields, ~45 min/metric)** on your 5–10 most-questioned metrics.

## Authoring workflow

- [ ] Collect source docs (see [guides/sourcing.md](https://github.com/keithbinkly/dbt-meta-context/blob/main/guides/sourcing.md) for field-by-field source map)
- [ ] Run distillation prompt — fills 60–70% of schema from existing docs
- [ ] Review output: verify `# NEEDS REVIEW` items; fill `# NOT FOUND` gaps with the metric owner (see [guides/interview.md](https://github.com/keithbinkly/dbt-meta-context/blob/main/guides/interview.md) for the domain-expert interview questions)
- [ ] Add `business_rules` (Layer 5) for any metric tied to a customer or regulatory SLA — absence creates false confidence
- [ ] Validate with `dbt-mc validate` — check for type errors and false-confidence risk
- [ ] Set `last_validated` to today's date

## The 5 layers

| Layer | Question | Failure it closes |
|-------|----------|------------------|
| 1. Context | Who cares and why does this exist? | Interpretation |
| 2. Expectations | What does good look like? | Calibration |
| 3. Investigation | When it breaks, where do I look? | Framing |
| 4. Relationships | What else moves when this moves? | Reasoning |
| 5. Decisions | What do I do about it? | Action + false confidence |

**Critical:** Layers 2–4 without Layer 5 create false confidence. An agent that knows healthy ranges but not business rules will give confidently wrong answers on SLA and compliance questions.

## Authoring principles

Follow the five principles in [guides/authoring.md](https://github.com/keithbinkly/dbt-meta-context/blob/main/guides/authoring.md):

1. Write for the worst-case consumer — no jargon, no assumed knowledge
2. Encode reasoning, not just facts (include the *why* in seasonality, investigation paths)
3. Use specific relationship types with direction, magnitude, and lag
4. Include magnitude in thresholds and seasonality
5. Write investigation paths as conditional logic (IF/THEN trees), not flat lists

## Validator

```bash
pip install "git+https://github.com/keithbinkly/dbt-meta-context.git#subdirectory=validator"
dbt-mc validate models/semantic_models/         # tier report + false-confidence risk
dbt-mc validate models/ --format json           # CI integration
```

Exit code 2 = false-confidence risk (expectations populated without `business_rules`).
See [validator/README.md](https://github.com/keithbinkly/dbt-meta-context/blob/main/validator/README.md) for CI and pre-commit setup.

## Reference

- Schema (all 36 fields): [spec/schema.md](https://github.com/keithbinkly/dbt-meta-context/blob/main/spec/schema.md)
- Distillation prompt (LLM extraction): [guides/distillation-prompt.md](https://github.com/keithbinkly/dbt-meta-context/blob/main/guides/distillation-prompt.md)
- Domain-expert interview guide (gap-filling): [guides/interview.md](https://github.com/keithbinkly/dbt-meta-context/blob/main/guides/interview.md)
- Sourcing guide (where to find each field): [guides/sourcing.md](https://github.com/keithbinkly/dbt-meta-context/blob/main/guides/sourcing.md)
- Authoring principles (with examples): [guides/authoring.md](https://github.com/keithbinkly/dbt-meta-context/blob/main/guides/authoring.md)
