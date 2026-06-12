# Field Extension Guide

How to evaluate whether new context belongs in the schema.

The schema is intentionally conservative. Every field represents a specific LLM reasoning failure that meta context prevents — adding fields that don't close a real failure inflates the schema without improving analytical accuracy.

## The four tests

Every proposed field must pass all four. Fail any one → don't add.

### Test 1: The failure test

**Question:** Does the absence of this context cause a specific, identifiable failure in LLM analytical reasoning?

- If yes → the field addresses a real gap
- If no → "nice to have" is not schema-worthy

**Method:** Construct a question where the answer depends on this context. Run the question WITH and WITHOUT the field populated. If the LLM's answer doesn't meaningfully change, the field doesn't earn its place.

### Test 2: The decay test

**Question:** Is this context at risk of being lost through personnel rotation, temporal drift, or inadequate storage?

- If easily re-derivable from data → belongs in automated metadata, not `meta:`
- If it lives in experts' heads → belongs in the schema
- If documented elsewhere durably → reference it, don't duplicate

### Test 3: The dual-audience test

**Question:** Is this field interpretable by both human analysts AND LLM agents without translation?

- Both must be able to parse and act on the field
- Only humans can use it → documentation, not schema
- Only machines can use it → technical metadata, not business context

### Test 4: The layer fit test

**Question:** Which layer's question does this context answer?

| Layer | Question |
|-------|----------|
| 1. Context | "Who cares and why does this exist?" |
| 2. Expectations | "What does good look like?" |
| 3. Investigation | "When it breaks, where do I look first?" |
| 4. Relationships | "What else moves when this moves?" |
| 5. Decisions | "What do I do about it?" |
| None of the above | New layer? Cross-cutting? Or out of scope? |

## Decision tree

```
Does absence cause an identifiable LLM failure?
├── NO → Don't add. Document as a metric note if needed.
└── YES →
    Is this context at risk of decay?
    ├── NO → Reference the existing source. Don't duplicate.
    └── YES →
        Is it interpretable by both humans and LLMs?
        ├── NO → Rework as natural language + typed structure.
        └── YES →
            Does it answer one of the 5 layer questions?
            ├── YES → Add to that layer. Follow existing key patterns.
            └── NO →
                Is this pattern present across 3+ distinct metrics?
                ├── NO → Document as a metric-specific note, not a schema field.
                └── YES → Propose as a new field or layer. Validate with eval.
```

## Worked examples

### Example: `data_freshness`

**Candidate:** `data_freshness: "Updated every 15 minutes via streaming pipeline"`

1. **Failure test:** Does an LLM give wrong answers without knowing freshness? Sometimes — but most analytical questions don't hinge on it. **Partial pass.**
2. **Decay test:** Freshness is derivable from pipeline metadata. **Fail.**
3. **Dual-audience:** Both can read it. **Pass.**
4. **Layer fit:** Closer to pipeline metadata than business context.

**Verdict:** Don't add. This belongs in dbt's `freshness:` config, not `meta:`.

### Example: `known_root_causes`

**Candidate:**
```yaml
known_root_causes:
  - date: "2025-11-15"
    description: "Black Friday carrier overwhelm"
    root_cause: "FedEx hub overflow"
    resolution: "Rerouted to UPS regional"
```

1. **Failure test:** Without this, an LLM investigating a November drop would miss the pattern and treat it as novel. **Pass.**
2. **Decay test:** Lives in post-mortem docs and senior analyst memory. Both decay. **Pass.**
3. **Dual-audience:** Human-readable narrative + structured fields. **Pass.**
4. **Layer fit:** "When it breaks, where do I look first?" → Layer 3. **Pass.**

**Verdict:** Add to Layer 3. Recommended tier.

## Proposing a new field

If a field passes all four tests, open an issue or PR with:

1. **Field name and type** — follow existing naming conventions
2. **Layer placement** — which question does it answer?
3. **Tier recommendation** — Core / Recommended / Optional, with rationale
4. **Failure demonstration** — a before/after eval showing the failure it closes
5. **Example value** — a realistic example from a real (or realistic synthetic) metric

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) for the full submission process.
