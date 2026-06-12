# Evaluation Methodology

How to run an ablation study on your own metrics.

## Overview

The eval tests how much analytical accuracy improves as meta context layers are added cumulatively. You create 6 YAML variants of the same metric (stripping layers from full → bare), ask 5 targeted questions against each, and score on 5 dimensions.

The core finding: adding layers produces measurable step-changes in response quality — and the absence of Layer 5 (Decisions) when Layer 2 (Expectations) is present creates false confidence, not just reduced quality.

---

## Step 1: Create 6 YAML variants

Starting from a fully-populated meta context block, create 6 cumulative variants by stripping layers:

| Variant | Contains | Layers present |
|---------|----------|---------------|
| V0 (bare) | Metric definition only — measures, dimensions, type_params | None |
| V1 (context) | V0 + `meta.context` | L1 |
| V2 (expectations) | V1 + `meta.expectations` | L1–2 |
| V3 (investigation) | V2 + `meta.investigation` | L1–3 |
| V4 (relationships) | V3 + `meta.relationships` | L1–4 |
| V5 (full) | V4 + `meta.decisions` | L1–5 |

---

## Step 2: Write 5 questions

One per failure type, tailored to the specific metric:

| # | Type | Template |
|---|------|----------|
| Q1 | Interpretation | "[metric_name] is [value] this week. What does this mean for the business?" |
| Q2 | Calibration | "[metric_name] is [value] this week. How concerned should we be?" |
| Q3 | Framing | "[metric_name] dropped [N points] (from [A] to [B]). What's likely driving this?" |
| Q4 | Decision | "[segment] has [metric_name] at [value]. Are we meeting our obligations?" |
| Q5 | Adversarial | "What was [metric NOT in YAML] last month?" |

Q5 tests hallucination resistance — the model should say "that information isn't in the semantic layer definition" rather than inventing a plausible answer.

---

## Step 3: Run each question against each variant

30 total runs (6 variants × 5 questions).

Controls:
- Same model across all runs
- Same system prompt
- Temperature 0 or consistent low temperature
- Record full responses, not just your interpretation

---

## Step 4: Score on 5 dimensions

Score each response 1–5 on all dimensions:

| Dimension | 1 | 3 | 5 |
|-----------|---|---|---|
| **Groundedness** | Invents or assumes values | References some context values | Cites exact values from YAML |
| **Calibration** | "This might be concerning" | Uses some thresholds | "Below healthy [0.94–0.99], above warning [0.92]" |
| **Diagnostic depth** | "Check the data" | Lists dimensions to check | Prioritized decision tree with branching logic |
| **Actionability** | Generic advice | Some specific steps | "Page fulfillment-ops on-call, check carrier dashboard" |
| **Hallucination resistance** | Invents plausible answers | Partially hedges | "This information isn't in the semantic layer definition" |

---

## Step 5: False confidence test

**This is the most important check.**

For Q4 (the decision question), compare V2 against V5:

- **V2 gives a confidently wrong answer** → the metric has a false-confidence risk. An agent with Layers 1–2 will sound authoritative on SLA questions but will answer from the wrong frame (calibration instead of contractual obligation).
- **V2 correctly refuses** ("I don't have SLA information to assess obligations") → safe for partial deployment at Bronze tier.
- **V5 gives the correct answer where V2 was wrong** → `business_rules` is earning its keep.

This is the key finding from the original eval: the dangerous state is not V0 (obviously insufficient) but V2 (calibrated but missing business rules). V2 answers with false confidence because it has expectations context to anchor to.

---

## Step 6: Produce a results summary

```markdown
## Results: [metric_name]

### Scoring matrix
| Variant | Q1 (interp) | Q2 (calib) | Q3 (frame) | Q4 (decision) | Q5 (adversarial) | Avg |
|---------|-------------|------------|------------|---------------|-----------------|-----|
| V0 | | | | | | |
| V1 | | | | | | |
| V2 | | | | | | |
| V3 | | | | | | |
| V4 | | | | | | |
| V5 | | | | | | |

### Step-changes
- Largest improvement: Layer [N] → [N+1] on [question type]
- Smallest improvement: Layer [N] → [N+1]

### False confidence test
- V2 on Q4: [confidently wrong / hedged / correct]
- V5 on Q4: [result]
- Risk: [safe for partial deployment / false confidence risk]

### Recommendations
- Priority fields to populate: [which fields produced biggest step-changes]
- Fields with no measurable impact: [which to defer]
```

---

## LLM feedback questionnaire

After each eval run, ask the model to self-report on the context it was given. This surfaces which fields felt insufficient and what the model would have found useful — valuable input for schema extensions.

```yaml
context_feedback:
  completeness:
    question: "Did the meta context contain everything you needed to answer the question?"
    options: [yes, mostly, partially, no]
    if_not_yes: "What specific information was missing?"

  relevance:
    question: "Was all provided context relevant to this question?"
    options: [all_relevant, mostly_relevant, some_irrelevant, mostly_irrelevant]
    if_not_all: "Which fields were not useful for this question?"

  interpretation:
    question: "Were any fields ambiguous or hard to interpret?"
    options: [all_clear, minor_ambiguity, significant_ambiguity]
    if_not_clear: "Which fields and what would make them clearer?"

  confidence_impact:
    question: "How did the context affect your confidence in your answer?"
    options: [high_confidence, moderate, low_despite_context, lower_than_without]
    explanation: "What drove your confidence level?"

  missing_connections:
    question: "Did you need to make inferences that could have been explicit?"
    freeform: true

  suggested_additions:
    question: "If you could add one field to the schema for questions like this, what would it be?"
    freeform: true
```

The suggested_additions responses are the best signal for schema extensions. If multiple distinct metrics, multiple models, and multiple questions all surface the same missing field — that's a candidate for the schema.

---

## Per-layer effectiveness signals

| Layer | Working when... | Failing when... |
|-------|----------------|-----------------|
| Context (1) | Agent identifies metric purpose, routes to right team | Agent describes the SQL formula instead of business meaning |
| Expectations (2) | Agent calibrates severity using thresholds | "I can't tell if this is good or bad" |
| Investigation (3) | Agent follows prioritized, branching investigation path | Lists all dimensions as equally valid |
| Relationships (4) | References correlated metrics and external events | Treats the metric in isolation |
| Decisions (5) | Cites business rules and action protocols | Generic advice, or false-confidence anchoring to healthy_range |
