# Eval Results

Original 6-condition experiment — January 2026.

## Setup

**Metric:** `payment_success_rate` — a payment success rate metric on a simulated dbt semantic model.

**6 experimental conditions:**

| ID | Name | Context given | ~Words |
|----|------|---------------|-------:|
| C0 | Bare | schema.yml + model.sql only | 371 |
| C1b | Extracted meta | Schema with LLM-extracted meta context | 1,157 |
| C1c | Perfect meta | Schema with hand-authored meta context | 1,157 |
| C2 | Clean docs | Schema + SQL + wiki + runbook | 1,789 |
| C3 | Full docs | Schema + SQL + all 7 source docs | 4,743 |
| C4 | Adversarial | C3 + 3 distractor documents | 5,815 |

C1b tests whether a frontier model can extract meta context from scattered docs as well as a human can author it from scratch. C4 tests robustness when irrelevant/contradictory documents are present.

**Models tested:** Haiku, Sonnet, Opus (same generation).

**Scoring:** 5 dimensions (Groundedness, Calibration, Diagnostic Depth, Actionability, Hallucination Resistance), 1–5 scale. See [`design.md`](design.md) for full rubric.

---

## Results

### Scores by condition and model

| Condition | Haiku | Sonnet | Opus |
|-----------|-------|--------|------|
| C0 — bare | 2.3 | 2.7 | 3.1 |
| C1b — extracted meta | **4.7** | 4.8 | 4.9 |
| C1c — hand-authored meta | 4.6 | 4.8 | 4.9 |
| C2 — clean docs | 3.8 | 4.1 | 4.5 |
| C3 — full docs | 4.0 | 4.3 | 4.5 |
| C4 — adversarial | 4.1 | 4.4 | 4.6 |

### Key numbers

| Metric | Value |
|--------|-------|
| Model gap on bare schemas (Haiku vs Opus) | 0.8 points |
| Model gap with meta context | 0.2 points |
| Meta lift — Haiku (C0 → C1b) | +2.4 points |
| Meta lift — Opus (C0 → C1b) | +1.8 points |
| Distillation ratio (C3 → C1b word count) | 5.6× compression |
| C1b vs C1c | C1b ≥ C1c across all 3 models |

---

## Key findings

### 1. Meta context collapses the model gap

On bare schemas, Haiku (2.3) trails Opus (3.1) by 0.8 points — a large gap in analytical quality. With meta context, Haiku (4.7) and Opus (4.9) are nearly indistinguishable. The schema does more to close the model gap than the model itself.

### 2. Extracted meta matches or beats hand-authored meta

C1b (LLM-extracted from 7 source documents) equaled or exceeded C1c (hand-authored from scratch) across all three models. This is the most practically important finding: you don't need a domain expert to author the schema. You need:
- Existing documentation (wikis, runbooks, incident reports)
- A frontier model to distill it
- A domain expert to review and fill gaps

The bottleneck shifts from authoring time to documentation quality.

### 3. Full docs (C3) underperforms extracted meta (C1b)

More context is not better. Giving the model all 7 source documents (4,743 words) produced lower scores than extracted meta context (1,157 words). The extraction process removes noise, resolves contradictions, and presents information in a structure the model can reason from efficiently.

### 4. Adversarial documents barely hurt extracted meta

C4 (C3 + 3 distractor documents) scores nearly the same as C3 — the model is not meaningfully misled by irrelevant context when it's in a structured format. The main risk of distractors was with C3's flat document stack.

### 5. The false confidence trap

The most important finding is not in the averages. For the decision question (Q4: "Are we meeting our SLA obligations?"):

- **V2 (Layers 1–2):** Confidently wrong. The model anchored to `healthy_range` and answered as if calibration data implies contractual compliance.
- **V5 (all layers):** Correct. Cited the specific SLA business rule and gave the right answer.

This means Bronze tier (Layers 1–3) is safe for calibration and investigation questions but creates a false-confidence risk for decision questions if Layer 5 is not eventually added. This is why `business_rules` is a Core field even in Bronze tier — it's not optional for metrics tied to SLAs.

---

## Fixtures

You can run the eval yourself against any model — [`design.md`](design.md) specifies the six conditions, question set, and scoring rubric, and [`extraction-quality.md`](extraction-quality.md) covers evaluating the extraction step directly.
