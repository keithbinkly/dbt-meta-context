# dbt-meta-context-validator

A CLI for validating meta context blocks in dbt semantic model YAML files.

## Install

```bash
pip install "git+https://github.com/keithbinkly/dbt-meta-context.git#subdirectory=validator"
```

Or from source:

```bash
cd validator/
pip install -e .
```

## Usage

```bash
# Validate a single file
dbt-mc validate models/semantic_models/my_metrics.yml

# Validate all semantic model files in a directory
dbt-mc validate models/semantic_models/

# Validate with JSON output (for CI integration)
dbt-mc validate models/ --format json

# Show only errors (suppress warnings)
dbt-mc validate models/ --errors-only
```

## Output

```
models/semantic_models/mart_payments.yml
  metric: success_rate
    ✓ Bronze tier: all 13 Core fields present
    ✗ Silver tier: missing recommended fields
        - expectations.trend (Recommended)
        - investigation.common_false_positives (Recommended)
        - relationships.leads_to (Recommended)
    ⚠ FALSE CONFIDENCE RISK: expectations populated without decisions.business_rules
        Layer 2 (Expectations) is present but Layer 5 (Decisions) has no business_rules.
        An AI agent with this context will give calibrated but potentially wrong answers
        on SLA and compliance questions. Add business_rules or remove expectations.

  metric: refund_rate
    ✓ Bronze tier
    ✓ Silver tier
    ✗ Type error: healthy_range must be [number, number], got string

Summary: 2 metrics | 1 Bronze | 1 Silver | 0 Gold | 1 false-confidence risk
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All metrics pass Bronze tier, no type errors, no false-confidence risk |
| 1 | One or more metrics fail Bronze tier or have type errors |
| 2 | False-confidence risk detected (Layer 2 present, Layer 5 `business_rules` absent) |

Exit code 2 does not imply 1 — a metric can be Bronze-compliant and still have a false-confidence risk.

## CI integration

```yaml
# .github/workflows/dbt-meta-context.yml
- name: Validate meta context
  run: dbt-mc validate models/semantic_models/ --format json > meta-context-report.json
  continue-on-error: true

- name: Check for false-confidence risks
  run: dbt-mc validate models/semantic_models/ --errors-only
```

Or as a dbt test hook — add to your `dbt_project.yml`:

```yaml
on-run-end:
  - "{{ log(run_results | tojson) }}"
```

(Full dbt test integration coming in a future release.)

## Pre-commit hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: meta-context-validate
        name: Validate dbt meta context
        entry: dbt-mc validate
        language: python
        files: \.yml$
        args: [--errors-only]
```

## Rules checked

| Rule | Tier | Description |
|------|------|-------------|
| Core fields present | Bronze | All 13 Core fields populated |
| healthy_range type | Bronze | Must be [number, number] |
| causal_dimensions structure | Bronze | Each entry must have name, why, priority |
| correlates_with relationship typed | Bronze | relationship must be a string describing direction/type |
| when_this_drops structure | Bronze | Each entry must have threshold and action |
| False confidence risk | Warning | Layer 2 present, Layer 5 business_rules absent |
| Recommended fields present | Silver | All 10 Recommended fields populated |
| last_validated freshness | Warning | Flag if > 90 days ago |
| All fields present | Gold | All 36 fields populated |
