# Prior Art: How This Compares to Other Context Layers

The semantic layer ecosystem has converged on "structured context for AI grounding" from many directions. This document maps the landscape and explains where the Meta Context Schema's claims survive.

---

## TL;DR

Every major semantic layer vendor has shipped some form of AI context. The floor is **Layer 1 (descriptions, synonyms, sample values)** — this is table stakes for text-to-SQL. The gap is the upper layers: healthy ranges, investigation paths, semantic metric-to-metric relationships, and action protocols.

More precisely, the gap is **evaluability** — whether the context layer is structured enough to drive refusals, coverage scoring, and regression testing. **Structured ≠ evaluable.** A single free-text blob (`ai_context: "use this metric for..."`) can't be linted for completeness, can't score coverage, can't fail a CI assertion when `business_rules` is missing.

The surviving claim: **the first discrete-field, multi-layer, coverage-measurable context schema for dbt MetricFlow** where upper layers drive refusal, CI assertion, and context coverage scoring — not just machine-readable text.

---

## Layer coverage matrix

`●` discrete fields · `◐` partial / technical-only / examples · `○` prose-only or absent

| Schema | L1 Interpret | L2 Calibrate | L3 Framing | L4 Reasoning | L5 Action | Free-text escape |
|--------|:---:|:---:|:---:|:---:|:---:|---|
| **Meta Context Schema** | ● | ● | ● | ● metric↔metric | ● | — (all discrete fields) |
| Snowflake Semantic Views | ● | ○ | ◐ verified queries | ◐ joins only | ○ | `custom_instructions` (prose) |
| Databricks metric views | ● | ◐ windowing | ○ | ◐ joins only | ○ | `comment` (prose) |
| Cube `meta.ai_context` | ● | ○ | ◐ drill_members | ◐ joins only | ○ | `ai_context` (prose) |
| Omni `ai_context` | ● | ○ | ◐ sample_queries | ○ | ○ | `ai_context` × model/view/field |
| Lightdash `ai_hint` | ● | ○ | ○ | ○ | ○ | `ai_hint` + agent `instruction` |
| dbt native (`meta`/desc) | ● | ○ | ○ | ◐ entities/ratio deps | ○ | generic `meta` dict |
| Wren AI MDL | ● | ○ | ◐ NL-SQL pairs | ● joins/hierarchies | ○ | `instructions.md` |
| Microsoft Prep-for-AI | ● | ◐ Q&A conditions | ◐ verified-answer filters | ◐ linguistic relations | ◐ verified answers | AI instructions (10k char) |
| GoodData Context Mgmt | ● | ○ | ◐ AI Memory | ○ | ◐ separate alert API | AI Memory (255 char) |
| Fivetran `agents_schema` † | ● | ○ | ○ | ◐ joins/lineage only | ○ | `ai_context` from LookML/OSI |
| Anthropic `data-context-extractor` skill | ◐ skill references | ○ | ◐ gotchas/query patterns | ◐ table relationships | ○ | Agent-side Markdown skill files |

### Discrete-field breadth by vendor

| Schema | Discrete field layers | If free-text prose counts |
|--------|:---:|:---:|
| **Meta Context Schema** | **5 / 5** | 5 / 5 |
| Microsoft Prep-for-AI | ~2 discrete + fragments | 5 / 5 |
| Wren AI MDL | 2 (L1, L4-joins) | 4 / 5 |
| Snowflake Semantic Views | 2½ (L1, L4-joins, ◐L3) | 3 / 5 |
| Cube / Databricks / GoodData | 1–2 | 3 / 5 |
| Omni / Lightdash / dbt native | 1 (L1) | 2–4 / 5 |
| Fivetran Agents Schema † | 1 (L1, L4-joins) | ~2 / 5 |

---

## Three findings from the comparison

### 1. Everyone owns L1. Almost no one reaches L2/L3/L5 as discrete fields.

Every schema has descriptions, synonyms, and sample values — because that's what **text-to-SQL translation** needs: which column, what's it called, what values exist. That floor is commoditized. The moment you ask for **what's a healthy value (L2), where to look when it breaks (L3), what to do about it (L5)** — the discrete-field support vanishes. Those layers exist in zero competitor schemas as first-class discrete fields. They survive only as prose in a free-text blob, if at all.

### 2. The "relationships" everyone has is the wrong kind.

Snowflake, Databricks, Wren, dbt, and Cube all have rich Layer 4 — but it's **physical join topology** (`left_table/right_table`, `join_type: MANY_TO_ONE`, entity foreign keys). That tells an LLM how to assemble a query. None of them encode **semantic metric-to-metric relationships** — `correlates_with` (typed: `inverse` / `leading-indicator` / `upstream-cause`), `leads_to`, `decomposes_into`, `affected_by {external_event, magnitude}`. The difference between "I can write the SQL" and "I understand that approval-rate and decline-rate are inverse and that this metric leads next week's chargebacks" is exactly this distinction. Reasoning ≠ joining.

### 3. The free-text blob is the universal escape hatch — and it's the tell.

`ai_context` (Cube, Omni), `ai_hint` (Lightdash), AI instructions (Microsoft, GoodData) — every vendor that addresses the upper layers does it with one unbounded free-text string. The blob has three costs a discrete-field schema avoids:

- **Re-parse tax:** the LLM must re-read and re-interpret prose every call instead of consuming addressable fields
- **Unvalidatable:** you can't lint "every metric has a healthy_range" on a prose blob — no coverage metric is definable
- **Doesn't compound:** prose doesn't enforce the extraction template that distills source docs into the same shape every time; a 36-field schema is a research-backed template, a blob is a freeform note

---

## Closest prior art, in detail

### arXiv 2604.25149 (April 2026)

*"Semantic Layers for Reliable LLM-Powered Data Analytics."* The closest academic corroboration of the core thesis. Benchmarks Claude Opus 4.7 / Sonnet 4.6 / GPT-5.4; finds that a 4KB hand-authored business-context markdown document improves LLM accuracy by +17–23pp. The paper validates the *approach* — business context on the semantic layer closes the gap. It doesn't specify a schema, doesn't define a coverage metric, and uses a freeform doc rather than discrete fields. Cite as corroboration: the empirical case is made; this schema is the discrete-field, version-controlled, coverage-measurable instantiation.

### Lightdash `ai_hint`

The closest dbt-native artifact: an AI-specific field *inside* dbt `meta:` at model, dimension, and metric level. Free text (single string or array), not a discrete-field taxonomy. This is the existence proof that AI-interpretation fields already live in `dbt meta:`. The Meta Context Schema's differentiation is a discrete 36-field taxonomy vs a single hint string.

### Snowflake Semantic Views

The strongest non-dbt boundary. A structured YAML schema with descriptions, synonyms on dims/facts/metrics, and verified queries (NL question + SQL) — explicitly positioned to improve AI accuracy. Different platform, less rich business-context taxonomy, but it is the clearest "someone shipped a structured LLM-grounding schema on a semantic layer." Snowflake's schema stops at L1 + join topology + verified query pairs. The Meta Context Schema's upper layers (calibration, investigation, action) don't exist in Snowflake Semantic Views.

### Fivetran Agents Schema †

A delivery/aggregation layer, not an authoring schema — the only such entry in this matrix. `agents_schema` doesn't *author* context; it materializes whatever dbt manifests + LookML + OSI already carry into queryable warehouse tables (`AGENTS.*`). It inherits the floor (L1 + join topology) and critically *strips depth on the way in*: `AGENTS.DBT_MODEL` keeps only fixed columns and **drops the arbitrary dbt `meta:` dict**, preserving only a denormalized OSI subset. Net: it represents the lower bound of the matrix — it re-exposes interpretation + lineage and discards the upper layers its own sources might hold. Its genuine novelty is on an axis this matrix doesn't otherwise track: **delivery** (context as warehouse tables an agent `SELECT`s, vs a `meta:` overlay). Open standard, MIT v0.0.6 (2026-05-29). Verified against landing page + repo + SPEC.md.

### Anthropic `data-context-extractor` skill

A genuine workflow precedent rather than a semantic-layer schema. Anthropic's `data-context-extractor` (in [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)) is a meta-skill that discovers warehouse schemas, interviews analysts, and generates company-specific agent skill files (`SKILL.md` plus Markdown references for entities, metrics, tables, gotchas, and sample queries). It captures the right human-extraction loop: entity disambiguation, primary identifiers, key metrics, standard filters, common gotchas, targeted iteration when an agent lacks domain context, and a pre-delivery quality checklist.

The boundary is artifact location and portability. The generated context lives agent-side in skill files and reference Markdown. It is not colocated with the dbt metric definition, not reviewed as part of the governed dbt project unless manually copied there, and not returned by the dbt Semantic Layer API. Meta Context Schema encodes the same class of tribal knowledge as discrete fields inside dbt `meta:` blocks, so it is version-controlled with the metric, validated in CI, auditable by git history, and available to any agent that consumes the Semantic Layer response.

### Cube `meta.ai_context` / Databricks / Wren MDL

Three more "AI context on the semantic layer" precedents. The category is real and named. Wren MDL is the closest in conceptual framing — it calls its own design "an open context layer for AI agents" and separates structural/semantic/business/operational/behavioral context including caveats and policies. It uses free-form instructions, not a discrete-field schema. GoodData's "Context Management" is literally named for this use case. In all three cases the upper layers exist as prose blobs with character limits; discrete-field support ends at L1.

---

## What this schema does not claim

- "No one has built structured context for AI." Snowflake, Lightdash, Cube, and others have.
- "No one has proposed the semantic layer as the right location." Wren MDL makes the same argument.
- "The semantic layer is the only place for AI context." Fivetran's Agents Schema puts it in warehouse tables.
- "No one has used analyst interviews or agent-side skills to capture data context." Anthropic's `data-context-extractor` does this in skill files; this schema's claim is governed, MetricFlow-native, discrete-field context returned through the Semantic Layer.
- "This is the first empirical validation of business context improving LLM accuracy." arXiv 2604.25149 (April 2026) beat us there.
- "This replaces a knowledge graph." The semantic layer is an executable graph for metric computation, not an open-world inference engine.
- "Authoring is the whole problem." Execution layers like Kaelio's ktx ("the context layer for data agents") consume context to run queries against the warehouse; this schema covers the authoring/governance side of what such tools read. Complementary jobs, not competitors.

---

## The defensible claim (paper-ready wording)

> *"We find no public implementation of a discrete-field, version-controlled business-context schema layered into dbt MetricFlow semantic-model YAML (`meta:` blocks) that encodes per-metric caveats, investigation paths, semantic metric-to-metric relationships, and action protocols as first-class discrete fields, paired with a measurable context-coverage evaluation. Existing work ships pieces — synonyms (Snowflake, Databricks), free-text AI hints (Lightdash, Cube, Omni), context-layer framing (Wren, GoodData), and the empirical case for business-context docs (arXiv 2604.25149) — but none combines the MetricFlow-native discrete-field schema, the anti-false-confidence field taxonomy, and the coverage metric."*

The market converges on a thin, interpretation-only context surface — sufficient for text-to-SQL, insufficient for analytical interpretation. Across nine production schemas, **calibration (healthy ranges, thresholds, seasonality), framing (causal dimensions, investigation paths, root-cause memory), and action (business rules, escalation) exist only as unstructured free text, if at all.** The one relationship primitive that is widely expressed as a discrete field — join cardinality — answers "how to assemble the query," not "how metrics move together."

---

*Verification note: field lists are from current vendor docs. Snowflake table-level `primary_key`/`synonyms` appear in concept/SQL docs but not the published YAML syntax block (spot-verify `verified_queries` and Cube `meta.ai_context` against current docs before citing in formal writing). Last updated 2026-06-09.*

*PRs welcome — if you've found a vendor implementation that belongs here, open one. Please verify the actual spec/docs, not marketing material.*
