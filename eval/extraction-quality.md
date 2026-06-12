# Extraction Quality Evaluation

The existing ablation eval measures downstream answer quality after a context card exists. Add a small direct eval for the extraction step itself: did the model recover the right fields from the source packet, cite them faithfully, identify missing evidence, and flag conflicts?

## When To Run

Run this after generating an extracted `meta:` block from `guides/distillation-prompt.md`, before using that block in the downstream answer-quality eval.

## Fixture

Use one metric with:

- Source packet: the exact docs given to the extraction model.
- Gold card: a human-reviewed `meta:` block for the same metric.
- Gold gap list: fields intentionally not supported by the source packet.
- Gold conflict list: known conflicts seeded in the source packet, if any.

The field-level coverage score requires a gold card. Citation presence can be checked mechanically. Citation correctness, semantic field correctness, and conflict quality require human review or an LLM judge with quoted source passages.

## Metrics

| Metric | What it measures | How to score | Mechanical? |
|--------|------------------|--------------|-------------|
| Field-level coverage | Percent of gold-card fields recovered with materially correct values | `correct_extracted_fields / supported_gold_fields` | No. Requires gold card plus human or LLM judge |
| Citation presence | Extracted values include a `# Source:` comment | `values_with_source_comment / extracted_values` | Yes |
| Citation fidelity | Citation actually supports the extracted value | Sample or full review against the cited passage | Partly. Retrieval can locate passages; support judgment needs human or LLM judge |
| Gap-detection accuracy | `# NOT FOUND` appears only where the source packet lacks support | Precision/recall against gold gap list | No. Requires gold gap list |
| Conflict-detection accuracy | Known contradictions are marked with `# CONFLICT` and not silently resolved | Precision/recall against gold conflict list | No. Requires seeded or known conflicts |

## Suggested Scoring Table

| Run | Model | Field coverage | Citation presence | Citation fidelity | Gap precision | Gap recall | Conflict precision | Conflict recall | Notes |
|-----|-------|----------------|-------------------|-------------------|---------------|------------|--------------------|-----------------|-------|
| `payment_success_rate` | `model-name` | | | | | | | | |

## Minimal Protocol

1. Create or choose a source packet and a human-reviewed gold card.
2. Run the distillation prompt at temperature 0.
3. Parse the output into field paths, values, comments, `# NOT FOUND`, and `# CONFLICT` markers.
4. Mechanically score citation presence and marker presence.
5. Review each extracted field against the gold card and cited source passage.
6. Report unsupported extractions separately from missing fields. Unsupported extractions are higher risk because they create false confidence.

## Pass/Fail Gate

For a prompt change to be accepted, require:

- No unsupported Layer 5 `business_rules` or action protocols.
- No silent resolution of known conflicts.
- Citation presence on every extracted non-empty field.
- Gap recall high enough that missing Layer 2 thresholds, Layer 3 investigation paths, and Layer 5 business rules are not missed.

Recommended starting thresholds for a small fixture:

| Check | Minimum |
|-------|---------|
| Field-level coverage on supported Core fields | 90% |
| Citation presence | 100% |
| Citation fidelity on Core fields | 95% |
| Gap recall on Core fields | 95% |
| Conflict recall for seeded conflicts | 100% |

Treat these as project gates, not scientific claims. With one fixture, they catch regressions in the extraction prompt. They do not prove general extraction quality across domains.
