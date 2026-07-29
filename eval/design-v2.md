# Eval v2 — The Asymmetry Experiment (design)

**Status:** DRAFT — pre-registration. Written 2026-07-17, before any v2 runs. Cross-family
hardening round pending; no numbers in this file may be cited until runs complete.
**Prior art:** [`design.md`](design.md) + [`results.md`](results.md) (January 2026, 6 conditions,
Haiku/Sonnet/Opus same-generation). v2 extends it; it does not replace the v1 record.

## Why a v2

The v1 eval established the *reading* half of the meta-context economics claim (context collapses
the reader-tier gap: 0.8 → 0.2 points) on a model generation that no longer exists at the
frontier. Three gaps motivate v2:

1. **The writing half was never ablated.** Every v1 card was frontier-extracted. No condition
   tested a cheap model as *author*. "Write with frontier, read with cheap" is therefore half
   claim, half assumption.
2. **No content-matched prose control.** v1's C2 ("clean docs") differed from the card in content
   AND form, so it cannot answer the strongest skeptic argument: LLMs read prose well, so the
   interpretive layer may not need structure at inference time.
3. **Single runs, one simulated metric, same-family judging.** No error bars; no protection
   against judge-family bias; n=1 metric.

Fable 5's release provides the first 4-tier same-family ladder (Fable 5, Opus 4.8, Sonnet 5,
Haiku 4.5), making a real author-tier × reader-tier factorial possible on one subscription.

## Claims under test

| # | Claim | Falsifiable statement |
|---|-------|----------------------|
| A | Reading equalization | With a Gold card, the cheapest reader's mean score is within 0.3 points of the frontier reader's; without it, the gap is ≥ 0.6. (Thresholds from v1; re-registered here before runs.) |
| B | Authoring asymmetry | Cards authored by Fable 5 produce higher downstream reader scores than cards authored by Haiku 4.5, by a margin exceeding 2× the seed-level standard deviation. (If NOT — the frontier-author premium is ~0 and the claim must be rewritten as "write once with any competent model.") |
| C | Structure > prose at inference | V5 (structured card) outscores P (same content, word-matched flat prose) for at least the two cheapest readers. (If NOT — structure's value is confined to governance/lint/coverage, and the article's counterargument paragraph becomes the headline, not the hedge.) |
| D | False-confidence persistence | On the V2-variant SLA question, at least the two cheapest readers still answer confidently-wrong (the v1 trap), and Layer 5 still corrects them. Explicitly test whether **Fable 5 escapes the trap unaided** — if frontier models now hedge correctly without Layer 5, the anti-false-confidence positioning must be scoped to non-frontier readers. |
| E | Structured pointer beats prose pointer | On registry-resolution questions (contract-scoped thresholds, issue #1's `expectations_source` pattern), the structured pointer yields a higher mechanical-correctness rate than the prose "see registry" pointer, at every reader tier. |

Every claim has a pre-registered failure interpretation. A failed claim is a finding, not a
discarded run.

## Design

### Factors

- **Reader (6):** Fable 5 · Opus 4.8 · Sonnet 5 · Haiku 4.5 · GPT-5.6 (codex) · Gemini 3.1 Pro (agy).
  The two cross-family readers guard against "the schema is tuned to Claude."
- **Author (3, Phase 2 only):** Fable 5 · Sonnet 5 · Haiku 4.5 — each extracts a card from the
  identical source-doc corpus, same extraction prompt, one shot (no retries; retries would blur
  the tier signal).
- **Context variant (6):**
  | ID | Contents |
  |----|----------|
  | V0 | bare schema (v1's C0) |
  | V2 | Layers 1–2 only (the false-confidence trap) |
  | V5 | full 5-layer card |
  | P  | V5 content flattened to prose, word-count within ±10% of V5, no field names/structure |
  | R-prose | V5 with nulled thresholds + prose registry pointer (Gap 1 workaround as documented) |
  | R-struct | V5 with nulled thresholds + structured `expectations_source` pointer (issue #1 proposal) |
- **Metric (2):**
  1. `payment_success_rate` (v1's fixture — continuity anchor; card refreshed, not reused verbatim).
  2. `punctuality_rate` — a transport-regulator KPI shaped like issue #1's deployment: per-contract
     + per-segment thresholds with validity windows, a 6-row `reg_contract_indicator` registry
     fixture. Gives claims D/E a mechanically checkable ground truth.
- **Questions (5 per metric):** v1's five failure-type questions (interpretation, framing,
  decision/SLA, relationship, adversarial), re-tailored per metric. For `punctuality_rate`, the
  decision question requires an actual registry lookup ("is contract CTR-001 meeting its
  reliability SLA on 2026-06-30?") with one correct answer derivable from the fixture.
- **Seeds:** 3 per cell (temperature 0.7). Report mean ± sd; a claim margin below 2× pooled sd is
  reported as "not established," never rounded up.

### Phases (to keep the grid tractable)

- **Phase 1 — reading (Claims A, C, D, E):** 6 readers × 6 variants × 5 questions × 3 seeds ×
  2 metrics = **1,080 reads**, using the Fable-authored card only.
- **Phase 2 — authoring (Claim B):** 3 authors × 2 metrics = 6 extractions; each card read by
  2 readers (Haiku 4.5 + Sonnet 5 — the economically relevant tiers) × 5 questions × 3 seeds ×
  V5 only = **180 reads**.
- Phase 2 runs only after Phase 1 sanity-checks pass (see Gates).

### Scoring

1. **Mechanical first, wherever ground truth exists:** the SLA/registry questions and the
   adversarial question ("what was [metric not in YAML]?") are scored pass/fail by string/number
   match + a refusal check — no judge involved. Mechanical scores are the primary evidence for
   claims D and E.
2. **Rubric scoring (v1's 5 dimensions, 1–5)** for everything else, by **two blind cross-family
   judges** (GPT-5.6 and Gemini 3.1 Pro). Blinding: responses are stripped of any mention of
   their condition, shuffled, and assigned opaque IDs before judging; judges never see two
   responses to the same question in the same call. Judge agreement (Pearson on the overlap set)
   is reported; if r < 0.6 the rubric is ambiguous and results are held until it's repaired.
   No Claude-family judge — every Claude tier is a subject.
3. **Cost accounting:** every read logs input/output tokens and model tier; results report
   **cost-per-quality-point** (rubric) and **cost-per-correct-decision** (mechanical) per cell —
   the economic claim stated as a number for the first time.

### Gates

- **G0 (fixtures):** both metrics' V5 cards pass `dbt-mc validate` at Bronze+ (R-variants pass via
  the intentional-null path); P-variant word count within ±10% of V5; registry fixture's correct
  answers derived by hand and written into `answers.json` before any model runs.
- **G1 (pilot):** 1 seed × Haiku × all variants × 1 metric. Checks harness plumbing, response
  parseability, and that V0 ≠ V5 is detectable at all. Abort and repair if not.
- **G2 (Phase 1 sanity):** judge agreement ≥ 0.6; seed-level sd < 0.8 rubric points (else raise
  seeds to 5 before proceeding).

### Execution

All tiers run headless on existing subscriptions — no API key:
- Claude tiers: `claude -p --model <id>` (fable/opus/sonnet/haiku ids per /model).
- GPT-5.6: `codex exec -m gpt-5.6-luna` (stdin-hang guard: `< /dev/null` / stdin-file pattern).
- Gemini: `agy --model "Gemini 3.1 Pro (High)" -p` (same guard).
Harness: a Workflow-orchestrated run (or plain bash fan-out) writing one JSONL row per read:
`{metric, variant, author, reader, question, seed, response, tokens_in, tokens_out, ts}`.
Judging is a second pass over the JSONL; mechanical scoring a third. Everything lands in
`eval/v2/` (fixtures, runs.jsonl, judged.jsonl, results-v2.md).

### Deliverables

- `eval/v2/` fixtures + raw runs (committed — the eval must be re-runnable by a stranger).
- `eval/results-v2.md` — findings against the five pre-registered claims, with error bars and
  cost tables; explicit "claim not established" language where margins are thin.
- Downstream consumers: the six-axis article's counterargument section (claim C), the Summit
  talk (claims A/B economics), issue #1's `expectations_source` RFC (claim E).

## Known limitations (pre-registered)

- n=2 metrics; one is synthetic-but-realistic. Findings generalize to the *shape* of the claims,
  not to all domains.
- One extraction shot per author tier (deliberate — retries blur the tier signal — but it means
  author-tier variance is unmeasured; noted as future work).
- Judges are also vendors' models; blind protocol mitigates but does not eliminate family taste.
- Temperature 0.7 with 3 seeds trades variance resolution for cost; G2 escalates to 5 seeds if sd
  demands it.
