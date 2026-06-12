# Contributing

## Schema extensions

The most important contribution is proposing new fields. The schema is intentionally conservative — every field represents a specific LLM reasoning failure that meta context prevents. Before opening a PR, read [`spec/field-guide.md`](spec/field-guide.md).

### Process

1. **Open an issue first** — describe the failure mode you've observed, what information would close it, and which layer it belongs to. This lets us align before you do the eval work.

2. **Run the 4-test framework** (from `spec/field-guide.md`) against your proposed field. All four tests must pass.

3. **Demonstrate with an eval** — follow the methodology in [`eval/design.md`](eval/design.md) with a fixture for your use case. Show the before/after scores. A proposed field without an eval demonstration will be held until one is provided.

4. **Submit a PR** that includes:
   - Updated `spec/schema.md` (field added to the right layer table with tier recommendation)
   - Updated `spec/field-guide.md` (worked example showing the 4-test pass)
   - Eval results (as a markdown file in `eval/`)
   - Updated `validator/meta_context_validator/rules.py` (type check for the new field if it has a typed structure)

### Tier assignment

| Tier | Criteria |
|------|----------|
| **Core** | Absence causes a failure demonstrated in eval. Any metric deployed without this field has a known analytical gap. |
| **Recommended** | Measurably improves one or more eval dimensions but absence doesn't create a specific, dangerous failure mode. |
| **Optional** | Useful for full organizational memory encoding. High-effort to populate. |

When in doubt, propose Recommended. We'd rather promote a field than demote one.

### Known gaps you can contribute to

Three high-priority schema gaps are documented in [`spec/known-gaps.md`](spec/known-gaps.md):

1. **Multi-tenancy** — per-contract threshold overlays without metric forking
2. **Schema versioning** — per-metric `schema_version` field and validator enforcement
3. **Temporal validity** — `valid_until` hard-expiry field

These are the most wanted contributions. Each gap document describes the problem, a current workaround, and the proposed extension shape. If you're deploying in a regulated or multi-tenant environment, your real-world use case is exactly what's needed to finalize the field design.

---

## What we're not looking for

- Fields that duplicate dbt's built-in YAML (description, tags, owner in config.meta)
- Fields derivable from warehouse queries (data freshness, row counts — these belong in pipeline metadata)
- Fields only interpretable by machines, not humans (binary flags, numeric codes without explanation)
- "Nice to have" context that doesn't close a specific failure mode

---

## Eval fixtures

New fixtures are very welcome. A good fixture:

- Uses a realistic (but fictional) metric from a real domain
- Includes at least 3-5 source documents representing different document types
- Has at least one intentional challenge (a contradiction, a distractor, missing context for one layer)
- Includes a `ground_truth.md` with 5 questions and gold-standard answers

Fixtures live in `eval/fixtures/<domain-metric-name>/`.

---

## Validator

The validator is intentionally minimal — it checks structure and completeness, not semantic quality. Contributions welcome:

- New type checks for existing fields
- A `--fix` mode that adds `# NOT FOUND` placeholders for missing fields
- dbt test integration
- Better output formatting

Open an issue before starting significant validator work so we can coordinate.

---

## Prior art additions

If you've found a vendor implementation, paper, or open-source project that belongs in `spec/prior-art.md`, open a PR. Please verify the implementation yourself (read the actual spec/docs) rather than describing it from memory or marketing material.

---

## Code of conduct

Be direct and specific. Vague feedback is hard to act on. Disagreement is fine; dismissal isn't. We're building a schema for a specific, narrow problem — scope creep PRs will be declined with an explanation.
