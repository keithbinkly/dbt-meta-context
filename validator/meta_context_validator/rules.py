"""Validation rules for meta context blocks."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class Finding:
    level: str  # "error", "warning", "info"
    rule: str
    message: str


@dataclass
class MetricResult:
    metric_name: str
    tier: str  # "none", "bronze", "silver", "gold"
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self):
        return [f for f in self.findings if f.level == "error"]

    @property
    def warnings(self):
        return [f for f in self.findings if f.level == "warning"]

    @property
    def has_false_confidence_risk(self):
        return any(f.rule == "false_confidence_risk" for f in self.findings)


CORE_FIELDS = {
    "context": ["purpose", "business_question", "owner"],
    "expectations": ["healthy_range", "warning_threshold", "critical_threshold", "seasonality"],
    "investigation": ["causal_dimensions", "investigation_path"],
    "relationships": ["correlates_with", "affected_by"],
    "decisions": ["when_this_drops", "business_rules"],
}

RECOMMENDED_FIELDS = {
    "context": ["stakeholders", "definition"],
    "expectations": ["trend", "target"],
    "investigation": ["common_false_positives", "known_root_causes"],
    "relationships": ["leads_to"],
    "decisions": ["when_this_spikes", "escalation_path"],
    "_cross_cutting": ["last_validated"],
}

_MISSING = object()


def _field_state(layer_data: dict, f: str) -> str:
    """Classify a field as populated / explicit_null / empty / absent.

    Distinguishing absent from explicit null matters: the Gap 1 workaround
    (contract-scoped thresholds) *recommends* `warning_threshold: null` with the
    registry documented in decisions.business_rules. An explicit null written to
    that spec must not be scored as a missing Core field. Also treats 0 / 0.0 /
    False as populated — they are real values, not gaps (a threshold of 0 is a
    threshold).
    """
    v = layer_data.get(f, _MISSING)
    if v is _MISSING:
        return "absent"
    if v is None:
        return "explicit_null"
    if isinstance(v, (str, list, dict)) and len(v) == 0:
        return "empty"
    return "populated"


def _null_is_justified(meta: dict[str, Any]) -> bool:
    """The Gap 1 workaround shape: expectations nulled out, with the external
    source of truth documented in decisions.business_rules."""
    return bool((meta.get("decisions") or {}).get("business_rules"))


def validate_metric(metric_name: str, meta: dict[str, Any]) -> MetricResult:
    findings = []

    # --- Bronze tier: Core fields ---
    bronze_pass = True
    for layer, fields in CORE_FIELDS.items():
        # `or {}` — a whole layer set to explicit null must not crash the walk
        layer_data = meta.get(layer) or {}
        for f in fields:
            state = _field_state(layer_data, f)
            if state == "populated":
                continue
            if state == "explicit_null" and layer == "expectations" and _null_is_justified(meta):
                # Intentional null per the Gap 1 workaround: value is scoped
                # externally (e.g. per contract/segment) and business_rules
                # says where. Counts as present for tier purposes.
                findings.append(Finding(
                    level="info",
                    rule="intentional_null",
                    message=(
                        f"{layer}.{f} is explicitly null with the external source "
                        "documented in decisions.business_rules (Gap 1 pattern: "
                        "contract-/segment-scoped values). Treated as present."
                    ),
                ))
                continue
            if state == "explicit_null":
                findings.append(Finding(
                    level="error",
                    rule="unjustified_null",
                    message=(
                        f"{layer}.{f} is explicitly null without justification. "
                        "Nulled expectations are valid only when "
                        "decisions.business_rules documents the external source of "
                        "the values (Gap 1 workaround); other layers do not accept "
                        "null. Populate the field or remove it."
                    ),
                ))
                bronze_pass = False
                continue
            findings.append(Finding(
                level="error",
                rule="missing_core_field",
                message=f"Missing Core field: {layer}.{f} (required for Bronze tier)",
            ))
            bronze_pass = False

    # --- Type checks (Bronze) ---
    expectations = meta.get("expectations") or {}
    healthy_range = expectations.get("healthy_range")
    if healthy_range is not None:
        if (
            not isinstance(healthy_range, list)
            or len(healthy_range) != 2
            or not all(isinstance(v, (int, float)) for v in healthy_range)
        ):
            findings.append(Finding(
                level="error",
                rule="type_error",
                message="expectations.healthy_range must be [number, number]",
            ))
            bronze_pass = False

    causal_dims = (meta.get("investigation") or {}).get("causal_dimensions") or []
    if isinstance(causal_dims, list):
        for i, dim in enumerate(causal_dims):
            for key in ("name", "why", "priority"):
                if key not in dim:
                    findings.append(Finding(
                        level="error",
                        rule="type_error",
                        message=f"investigation.causal_dimensions[{i}] missing required key: {key}",
                    ))
                    bronze_pass = False

    correlates = (meta.get("relationships") or {}).get("correlates_with") or []
    if isinstance(correlates, list):
        for i, c in enumerate(correlates):
            if "relationship" not in c or not c.get("relationship"):
                findings.append(Finding(
                    level="error",
                    rule="type_error",
                    message=f"relationships.correlates_with[{i}] missing typed relationship",
                ))
                bronze_pass = False

    when_drops = (meta.get("decisions") or {}).get("when_this_drops") or []
    if isinstance(when_drops, list):
        for i, w in enumerate(when_drops):
            for key in ("threshold", "action"):
                if key not in w:
                    findings.append(Finding(
                        level="error",
                        rule="type_error",
                        message=f"decisions.when_this_drops[{i}] missing required key: {key}",
                    ))
                    bronze_pass = False

    # --- False confidence check ---
    has_expectations = bool(expectations.get("healthy_range") or expectations.get("warning_threshold"))
    has_business_rules = _null_is_justified(meta)
    if has_expectations and not has_business_rules:
        findings.append(Finding(
            level="warning",
            rule="false_confidence_risk",
            message=(
                "FALSE CONFIDENCE RISK: expectations populated without decisions.business_rules. "
                "An AI agent will give calibrated but potentially wrong answers on SLA/compliance "
                "questions. Add business_rules or document that no SLA applies."
            ),
        ))

    # --- Silver tier: Recommended fields ---
    silver_pass = bronze_pass
    for layer, fields in RECOMMENDED_FIELDS.items():
        if layer == "_cross_cutting":
            for f in fields:
                if not meta.get(f):
                    findings.append(Finding(
                        level="info",
                        rule="missing_recommended_field",
                        message=f"Missing Recommended field: {f} (required for Silver tier)",
                    ))
                    silver_pass = False
        else:
            layer_data = meta.get(layer) or {}
            for f in fields:
                if _field_state(layer_data, f) != "populated":
                    findings.append(Finding(
                        level="info",
                        rule="missing_recommended_field",
                        message=f"Missing Recommended field: {layer}.{f} (required for Silver tier)",
                    ))
                    silver_pass = False

    # --- Staleness check ---
    last_validated = meta.get("last_validated")
    if last_validated:
        try:
            validated_date = datetime.strptime(str(last_validated), "%Y-%m-%d").date()
            days_ago = (date.today() - validated_date).days
            if days_ago > 90:
                findings.append(Finding(
                    level="warning",
                    rule="stale",
                    message=f"last_validated is {days_ago} days ago (>90). Consider refreshing.",
                ))
        except ValueError:
            findings.append(Finding(
                level="warning",
                rule="stale",
                message=f"last_validated has invalid date format: {last_validated}",
            ))

    # --- Determine tier ---
    if not bronze_pass:
        tier = "none"
    elif not silver_pass:
        tier = "bronze"
    else:
        tier = "silver"  # Gold detection (all optional fields) not yet implemented

    return MetricResult(metric_name=metric_name, tier=tier, findings=findings)
