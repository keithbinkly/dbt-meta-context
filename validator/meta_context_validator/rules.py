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


def validate_metric(metric_name: str, meta: dict[str, Any]) -> MetricResult:
    findings = []

    # --- Bronze tier: Core fields ---
    bronze_pass = True
    for layer, fields in CORE_FIELDS.items():
        layer_data = meta.get(layer, {})
        for f in fields:
            if not layer_data.get(f):
                findings.append(Finding(
                    level="error",
                    rule="missing_core_field",
                    message=f"Missing Core field: {layer}.{f} (required for Bronze tier)",
                ))
                bronze_pass = False

    # --- Type checks (Bronze) ---
    expectations = meta.get("expectations", {})
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

    causal_dims = meta.get("investigation", {}).get("causal_dimensions", [])
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

    correlates = meta.get("relationships", {}).get("correlates_with", [])
    if isinstance(correlates, list):
        for i, c in enumerate(correlates):
            if "relationship" not in c or not c.get("relationship"):
                findings.append(Finding(
                    level="error",
                    rule="type_error",
                    message=f"relationships.correlates_with[{i}] missing typed relationship",
                ))
                bronze_pass = False

    when_drops = meta.get("decisions", {}).get("when_this_drops", [])
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
    has_business_rules = bool(meta.get("decisions", {}).get("business_rules"))
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
            layer_data = meta.get(layer, {})
            for f in fields:
                if not layer_data.get(f):
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
