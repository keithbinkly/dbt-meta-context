# Known Gaps and Open Problems

These are schema limitations we know about and are actively working on. They are documented here so:

1. Adopters in regulated or multi-tenant environments can design around them
2. Contributors know which problems are high-priority
3. We don't accept PRs that partially address a gap and create false assurance

---

## Gap 1: Multi-tenancy / per-contract threshold overlays

**Status:** Largely resolved by modeling practice (the tidy rule); `contract_overlays` RFC remains as the fallback for high-cardinality cases
**Raised by:** Production deployment in regulated public-transport domain

### The problem

The schema assumes single-tenant context: one set of thresholds, one set of business rules, one set of `when_this_drops` actions. This breaks in multi-tenant systems where different contracts, clients, or regulatory regimes require different alert thresholds for the same underlying metric.

Example: a payment authorization rate metric that should alert at 92% for consumer cards but 96% for commercial cards due to different SLA contracts. The current schema has no way to encode both without forking the metric entirely.

### Recommended practice: split the metric (the tidy rule)

In most cases this is a semantic-model design problem, not a missing schema feature. If `business_rules` or `when_this_drops` differ by segment value, you have two decision objects wearing one metric's name — and the fix is MetricFlow's own mechanism, a filtered metric per regime:

```yaml
metrics:
  - name: consumer_auth_rate
    filter: "{{ Dimension('transaction__card_tier') }} = 'consumer'"
    meta: { ... }   # one healthy range, one SLA, one runbook
  - name: commercial_auth_rate
    filter: "{{ Dimension('transaction__card_tier') }} = 'commercial'"
    meta: { ... }   # its own regime, its own card
```

Each contract-bearing population gets its own metric and its own card; the blended metric stays for cross-segment comparison with a thin card that points to the per-regime metrics via `decomposes_into`. Full statement of the rule and its scope condition (SLA-bearing populations must be tidy; descriptive metrics may stay blended): [`../guides/authoring.md`](../guides/authoring.md), "One decision regime per card."

This resolves the example above completely: `consumer_auth_rate` alerts at 0.92, `commercial_auth_rate` at 0.96, no forked logic, no overlay machinery.

### When the split doesn't scale

The tidy rule assumes a small number of regimes. With **hundreds of contracts** (true per-client SLAs rather than a handful of tiers), per-contract metrics proliferate beyond what a semantic layer can reasonably govern. That is the case the `contract_overlays` RFC below still targets — and where we most need real-world examples.

### Workaround for blended metrics you can't split yet

Null out the system-level threshold fields (`healthy_range`, `warning_threshold`, `critical_threshold`) and document in `business_rules` that thresholds are contract-scoped:

```yaml
meta:
  expectations:
    healthy_range: null  # contract-scoped — see business_rules
    warning_threshold: null
  decisions:
    business_rules: |
      Thresholds vary by contract tier.
      Consumer: alert at <0.92. Commercial: alert at <0.96.
      See contract_sla_registry table for per-client values.
    when_this_drops:
      - threshold: "contract-specific — see business_rules"
        action: "Query contract_sla_registry for client threshold, then page on-call"
```

This signals to the AI agent that a blanket numeric threshold would be wrong, and points to the external source of truth.

### Fallback schema extension (RFC stage — high-cardinality contracts only)

A `contract_overlays` key on `decisions` that provides per-tier threshold overrides:

```yaml
decisions:
  business_rules: "Base policy..."
  contract_overlays:
    - tier: consumer
      expectations:
        warning_threshold: 0.92
        critical_threshold: 0.88
      when_this_drops:
        - threshold: 0.92
          action: "Page mobile-wallet on-call"
    - tier: commercial
      expectations:
        warning_threshold: 0.96
        critical_threshold: 0.94
      when_this_drops:
        - threshold: 0.96
          action: "Notify enterprise team via PagerDuty P2"
```

If you're interested in contributing this, open an issue with your use case. We want at least 2-3 real-world examples before freezing the field structure.

---

## Gap 2: Schema versioning

**Status:** Partial — no frozen v1, no per-metric version pins  
**Raised by:** Regulated domain adopters who need to pin to a declared stable surface

### The problem

The schema is at v0.1.0 (see `CHANGELOG.md`). There is no mechanism for a metric to declare "this meta block conforms to schema v0.1.0" and be validated against that specific version's rules — useful for regulated environments where schema changes need an impact audit before adoption.

### What exists today

`CHANGELOG.md` declares the current schema version and what changed. The validator pins to the installed package version. There is no per-metric `schema_version` field.

### Roadmap

The current plan:

1. **v1.0.0 declaration** — when Core fields stabilize (no additions, no removals expected for 6+ months), we'll declare a frozen v1 with a stronger compatibility commitment
2. **Per-metric `schema_version` field** — promote `schema_version` to Optional, then Recommended once validator enforcement is stable:

```yaml
meta:
  schema_version: "0.1.0"
  context:
    purpose: "..."
```

The validator would warn (not error) if `schema_version` is absent, and error if the declared version doesn't match a known schema release.

### Workaround (current best practice)

Pin the `dbt-meta-context-validator` package to a specific version in your CI:

```yaml
# requirements.txt or pyproject.toml
dbt-meta-context-validator==0.1.0
```

This ensures your validation rules don't shift under a scheduled CI run. The schema fields themselves won't change without a version bump and CHANGELOG entry.

---

## Gap 3: Temporal validity

**Status:** Partial — `last_validated` exists, no `valid_until` or automatic expiry  
**Raised by:** Regulated domain adopters with required re-validation cycles

### The problem

`last_validated` (Optional field, ISO date) records when the meta block was last reviewed. It does not encode *when it expires*. A business rule that says "SLA requires 99.2% uptime" may be contractually bound to expire on a specific date, or may be wrong 90 days after a contract renewal. The validator flags staleness at 90 days but doesn't know what "stale" means for your domain.

### Proposed field: `valid_until`

```yaml
meta:
  last_validated: "2026-03-01"
  valid_until: "2026-09-01"  # optional; triggers error (not warning) after this date
```

The validator behavior:
- `valid_until` absent + `last_validated` > 90 days: warning (current behavior)
- `valid_until` present + today < `valid_until`: clean
- `valid_until` present + today ≥ `valid_until`: **error** (exit code 1), not just a warning

This lets regulated environments set hard expiry gates in CI without waiting for the 90-day staleness heuristic.

### Workaround (current best practice)

Add `valid_until` to your `business_rules` prose and handle it in your team's review cadence:

```yaml
decisions:
  business_rules: |
    SLA contract expires 2026-09-01. Re-validate before renewal.
  review_cadence: "quarterly"
```

Set a calendar reminder to re-run the validator before the expiry date. The 90-day staleness warning will fire automatically at that point.

---

## Gap 4: Context flooding at query time

**Status:** Open — no current mechanism

### The problem

The schema's design is optimized for single-metric queries — one context card, one metric definition, one question. In production, agents often handle multi-metric queries: "Compare our payment success rate and auth approval rate this week and tell me what's driving the divergence." At Gold tier (36 fields, roughly 900–1,400 tokens per card), loading several full cards consumes a large share of the model's effective attention budget before the user's question even enters the context window.

There are two concrete failure modes:

1. **Full-card fan-out.** An orchestration layer loads all cards for all metrics the query mentions. With 10+ metrics in a dashboard query, this floods the model and produces results comparable to the C3 (full docs) condition — which scored 0.7 points lower than extracted meta context (C1b) in the original eval.

2. **Cross-metric confusion.** When multiple cards are loaded simultaneously, the model can conflate `investigation_path` entries or `business_rules` from different metrics, especially when the cards share similar structure and domain vocabulary.

The schema has no mechanism to signal which layers or fields are high-priority for selective retrieval. Every field looks equally authoritative to an orchestrator that hasn't read [`../guides/authoring.md`](../guides/authoring.md).

### Workaround (current best practice)

Implement selective retrieval at the orchestration layer. Load layers selectively based on question type:

| Question type | Load for all mentioned metrics | Load only for primary metric |
|--------------|-------------------------------|------------------------------|
| Calibration ("is X normal?") | Layer 1 + Layer 2 only | — |
| Investigation ("why is X dropping?") | Layer 1 | Layers 3–4 |
| Action ("what should we do?") | Layer 1 | Layers 2–5 |
| Compliance ("are we meeting SLA?") | Layer 1 | Layer 5 only |

Implementation pattern:

```python
def load_card(metric_name: str, question_type: str, is_primary: bool) -> dict:
    card = fetch_meta_block(metric_name)
    if is_primary:
        return card  # full card for the metric the question is about
    # Secondary metrics: context layer + calibration essentials only
    return {
        "context": card.get("context", {}),
        "expectations": {
            k: v for k, v in card.get("expectations", {}).items()
            if k in ("healthy_range", "warning_threshold")
        }
    }
```

### Proposed schema extension (RFC stage)

A retrieval-hints annotation on the card, indicating which layers are essential vs. supplementary for multi-metric contexts:

```yaml
meta:
  _retrieval_hints:
    always_include: ["context", "expectations"]     # load for any mention
    include_for_primary: ["investigation", "relationships", "decisions"]
    include_when:
      - question_type: "compliance"
        layers: ["decisions"]
```

This is a metadata annotation on the card, not a new YAML block visible to MetricFlow. It gives orchestrators a machine-readable signal without requiring them to parse the authoring guide.

If you're building a multi-metric orchestration layer and have data on which selective retrieval strategies work best, open an issue. We want 2–3 real-world deployment examples before designing the field structure.

---

## Contributing to gap resolution

These four gaps are the highest-priority schema extensions. If you're working in a domain that exposes one of them, open an issue with your use case. The [field guide](field-guide.md) 4-test framework still applies — a proposed extension needs to demonstrate a specific failure mode that the gap causes, with before/after eval scores.

We'd rather document known gaps clearly than ship premature schema extensions that create their own problems.
