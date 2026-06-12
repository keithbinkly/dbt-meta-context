# Changelog

All notable changes to the Meta Context Schema are documented here.

Format: [Semantic Versioning](https://semver.org/). Breaking changes to the Core field set will increment the major version. New fields (Recommended or Optional) increment the minor. Bug fixes to the validator or documentation increment the patch.

---

## [0.1.2] — 2026-06-12

Positioning, attachment model, and install-path release. **No schema field changes.**

### Added

- **The tidy rule** — `guides/authoring.md` "One decision regime per card": Layer 2 may vary by segment (`segment_expectations` as calibration lookup); Layer 5 varying by segment is the signal to split the metric via MetricFlow filtered metrics. Scope condition: SLA-bearing populations must be tidy; descriptive metrics may stay blended.
- **Three-tier attachment** — `spec/schema.md` placement section now covers model (shared) / metric (specific) / **dimension (glossary card:** `definition`, `aliases`, `value_aliases`, `gotchas` via `config.meta`**)**. Round-trip verified: dimension `config.meta` parses under dbt Fusion and lands in `semantic_manifest.json`; the Semantic Layer API carries a per-dimension `metadata` field for it.
- `spec/osi-mapping.md` — all 36 fields mapped to OSI `ai_context` (one direct, ~five lossy, thirty with no OSI home), with an input-not-fork posture.
- README "Relationship to existing standards" block (OSI / dbt `meta:` / Agents Schema / execution layers).
- `examples/order_success_rate.yml` — the quick-start card as a validator-ready file (validates as Bronze).
- MIT `LICENSE` file.

### Changed

- **Gap 1 (multi-tenancy) largely resolved by the tidy rule**: per-regime filtered metrics are the recommended practice; `contract_overlays` RFC demoted to fallback for high-cardinality contract sets.
- README reframed product-first: capability tagline, skills.sh badge, agent-skill and validator install paths at the top.
- Skill SKILL.md links are absolute GitHub URLs (relative links broke when the skill was copied into consumer projects).

### Fixed

- **Validator CLI**: `dbt-mc validate <path>` now works as documented (the CLI previously only accepted `dbt-mc <path>`; `validate` is now a real subcommand).
- **Install instructions**: the package is not on PyPI; all docs now use the working `pip install "git+https://...#subdirectory=validator"` form.
- Stale `eval/fixtures/` reference in `eval/results.md`; broken relative link in CHANGELOG.

---

## [0.1.1] — 2026-06-11

Documentation and tooling release. **No schema field changes** — the Core key set declared stable in 0.1.0 is unchanged.

### Added

- `skills/authoring-meta-context/` — installable agent skill wrapping the authoring workflow (`npx skills add ... --skill authoring-meta-context`). A navigation layer over the guides; the guides remain the canonical content.
- `guides/interview.md` — domain-expert interview guide: per-layer questions with "listen for" notes, for the fields documents rarely contain (`investigation_path`, `business_rules`, `aliases`, false positives, escalation detail).
- `eval/extraction-quality.md` — how to directly evaluate the extraction step (field coverage, citation fidelity, gap detection, conflict detection), complementing the downstream answer-quality eval.
- `guides/distillation-prompt.md` — Step 0 source coverage declaration (the model inventories source sufficiency per layer *before* extracting) and a pre-merge quality checklist.
- `guides/sourcing.md` — warehouse preflight step (ground threshold interviews in actual distributions), Layer 2 preflight checks, and a batch source coverage map with false-confidence risk column.
- `guides/authoring.md` — context budget guidance (per-tier token estimates, selective retrieval for multi-metric queries), trust/staleness guidance (staleness half-life by field, prompt-injection review for externally-sourced cards), post-authoring verification checklist, card maintenance workflow with symptom-to-field diagnosis, common rationalizations, and red flags.
- `spec/known-gaps.md` — Gap 4: context flooding at query time, with a selective-retrieval workaround and a `_retrieval_hints` RFC stub.
- `spec/prior-art.md` — Anthropic `data-context-extractor` skill added to the layer coverage matrix and detailed prior art (agent-side skill files vs governed in-YAML context).

### Changed

- `guides/authoring.md` sourcing checklist deduplicated into a pointer to `guides/sourcing.md`.

---

## [0.1.0] — 2026-06-09

Initial public release. This is the schema as described in the [eval](eval/) and validated in a production financial-services deployment.

### Schema (36 fields across 5 layers)

**Core fields (Bronze tier — 13 fields)**

| Layer | Field |
|-------|-------|
| context | `purpose`, `business_question`, `owner` |
| expectations | `healthy_range`, `warning_threshold`, `critical_threshold`, `seasonality` |
| investigation | `causal_dimensions` (schema: `{name, why, priority}`), `investigation_path` |
| relationships | `correlates_with` (schema: `{metric, relationship}`), `affected_by` |
| decisions | `when_this_drops` (schema: `{threshold, action}`), `business_rules` |

**Recommended fields (Silver tier — +10 fields)**

| Layer | Field |
|-------|-------|
| context | `stakeholders`, `definition` |
| expectations | `trend`, `target` |
| investigation | `common_false_positives`, `known_root_causes` |
| relationships | `leads_to` |
| decisions | `when_this_spikes`, `escalation_path` |
| (cross-cutting) | `last_validated` |

**Optional fields (Gold tier — +13 fields)**

| Layer | Field |
|-------|-------|
| context | `aliases`, `granularity`, `tags`, `data_sources` |
| expectations | `baseline_date`, `volatility` |
| investigation | `data_quality_gotchas` |
| relationships | `decomposes_into`, `leads_to` (if not Silver) |
| decisions | `escalation_path` (if not Silver), `review_cadence`, `on_call_runbook` |
| (cross-cutting) | `notes`, `schema_version` |

### Validator (`dbt-meta-context-validator` 0.1.0)

- `dbt-mc validate <path>` — checks Bronze Core completeness and field structure
- Exit codes: 0 (clean), 1 (below Bronze or type error), 2 (false-confidence risk)
- False-confidence check: warns when `expectations.*` is populated without `decisions.business_rules`
- Staleness check: warns when `last_validated` > 90 days ago
- Supports model-level + metric-level meta merge (metric wins on conflict)
- `--format json` for CI integration
- `--errors-only` to suppress info-level findings

### Known gaps at release

Three schema limitations are documented in [`spec/known-gaps.md`](spec/known-gaps.md):

1. **Multi-tenancy**: no mechanism for per-contract threshold overlays without metric forking
2. **Schema versioning**: no per-metric `schema_version` field; regulated adopters should pin the validator package version
3. **Temporal validity**: `last_validated` exists; `valid_until` (hard expiry) does not yet

### Eval results

Full results at [`eval/results.md`](eval/results.md). Key numbers from the 6-variant × 5-question × 5-dimension ablation:

- Bare YAML (V0): 0.2 on calibration, 0.1 on decision-quality
- Full meta (V5): 0.9 on calibration, 0.8 on decision-quality
- Haiku + full meta (4.7) > Opus + docs (4.6): capability gap closes with structured context
- Distillation from source docs: 5.6× compression, LLM-extracted meta (C1b) matches hand-authored meta (C1c)

---

## Versioning commitment

**Before v1.0.0:** fields may be added (minor bump) or reclassified between tiers (minor bump). Core fields will not be removed without a deprecation cycle. The validator will not introduce new exit-code-1 or exit-code-2 conditions without a minor version bump.

**At v1.0.0:** Core field set declared stable. Breaking changes to Core field names, types, or required structure increment the major version with a migration guide.

Pinning the validator package version is the most reliable way to freeze validation behavior while the schema is pre-v1.
