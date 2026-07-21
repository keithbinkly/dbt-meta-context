"""Tests for validation rules — including the explicit-null semantics from issue #1.

The Gap 1 workaround (spec/known-gaps.md) recommends writing contract-scoped
expectations as explicit nulls with the external registry documented in
decisions.business_rules. Issue #1 reported that the validator scored that
exact pattern as missing_core_field errors (tier "none"). These tests pin the
corrected behavior: absent ≠ intentionally null.
"""

import copy

from meta_context_validator.rules import validate_metric


def _full_meta() -> dict:
    """A meta block that passes Bronze cleanly."""
    return {
        "context": {
            "purpose": "Share of trips completing on time under the service contract",
            "business_question": "Is the operator meeting contractual punctuality?",
            "owner": "service-quality-team",
        },
        "expectations": {
            "healthy_range": [90, 100],
            "warning_threshold": 92,
            "critical_threshold": 90,
            "seasonality": "Dips 1-2pts in winter months due to weather delays",
        },
        "investigation": {
            "causal_dimensions": [
                {"name": "line", "why": "Delays cluster by line", "priority": 1},
            ],
            "investigation_path": "IF network-wide: check weather. IF line-specific: check roadworks.",
        },
        "relationships": {
            "correlates_with": [
                {"metric": "reliability", "relationship": "inverse — cancellations depress punctuality denominator"},
            ],
            "affected_by": ["weather", "roadworks"],
        },
        "decisions": {
            "when_this_drops": [
                {"threshold": 90, "action": "Notify contract manager; penalty computation per registry"},
            ],
            "business_rules": "Thresholds and penalties are set per contract; see reg_contract_indicator.",
        },
    }


def _errors(result, rule=None):
    errs = result.errors
    if rule:
        errs = [f for f in errs if f.rule == rule]
    return errs


def test_fully_populated_passes_bronze():
    result = validate_metric("punctuality", _full_meta())
    assert result.tier != "none"
    assert not _errors(result)


def test_gap1_workaround_nulled_expectations_pass_bronze():
    """The issue #1 regression: explicit nulls + business_rules must validate clean."""
    meta = _full_meta()
    meta["expectations"]["healthy_range"] = None
    meta["expectations"]["warning_threshold"] = None
    meta["expectations"]["critical_threshold"] = None
    result = validate_metric("punctuality", meta)
    assert not _errors(result), [f.message for f in result.errors]
    assert result.tier != "none"
    infos = [f for f in result.findings if f.rule == "intentional_null"]
    assert len(infos) == 3


def test_explicit_null_without_business_rules_errors():
    meta = _full_meta()
    meta["expectations"]["warning_threshold"] = None
    meta["decisions"]["business_rules"] = ""
    result = validate_metric("punctuality", meta)
    assert _errors(result, "unjustified_null")
    assert result.tier == "none"


def test_absent_field_still_errors():
    meta = _full_meta()
    del meta["expectations"]["warning_threshold"]
    result = validate_metric("punctuality", meta)
    assert _errors(result, "missing_core_field")
    assert result.tier == "none"


def test_null_outside_expectations_errors_even_with_business_rules():
    meta = _full_meta()
    meta["context"]["purpose"] = None
    result = validate_metric("punctuality", meta)
    assert _errors(result, "unjustified_null")
    assert result.tier == "none"


def test_zero_values_are_populated_not_missing():
    """0 is a value, not a gap — the falsy-check latent bug."""
    meta = _full_meta()
    meta["expectations"]["warning_threshold"] = 0
    meta["expectations"]["critical_threshold"] = 0.0
    meta["expectations"]["healthy_range"] = [0, 5]
    result = validate_metric("punctuality", meta)
    assert not _errors(result), [f.message for f in result.errors]


def test_empty_string_and_list_count_as_missing():
    meta = _full_meta()
    meta["context"]["purpose"] = ""
    meta["relationships"]["affected_by"] = []
    result = validate_metric("punctuality", meta)
    assert len(_errors(result, "missing_core_field")) == 2


def test_false_confidence_warning_unchanged():
    meta = _full_meta()
    meta["decisions"]["business_rules"] = ""
    result = validate_metric("punctuality", meta)
    assert result.has_false_confidence_risk


def test_nulled_expectations_do_not_trigger_false_confidence():
    meta = _full_meta()
    meta["expectations"]["healthy_range"] = None
    meta["expectations"]["warning_threshold"] = None
    result = validate_metric("punctuality", meta)
    assert not result.has_false_confidence_risk
