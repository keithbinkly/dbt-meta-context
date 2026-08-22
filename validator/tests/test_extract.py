"""Tests for metric extraction across the two YAML shapes dbt projects use.

dbt Fusion's inline spec puts the card on `models[].config.meta` and the
metrics on `models[].metrics[]` with their own `config.meta`. The extractor
originally read only the legacy `models[].semantic_model.metrics[].meta` and
top-level `metrics[].meta`, so a fully populated Fusion file validated as
"Summary: 0 metrics" and exited 0 — a false clean, the worst possible failure
for a CI gate. These tests pin both shapes.

The Fusion fixture mirrors the layout dbt Fusion emits (model-level
card + per-metric cards + a `semantic_model` stub holding only enabled/name);
the content is synthetic.
"""

import yaml
from click.testing import CliRunner

from meta_context_validator.cli import _extract_metrics, main
from meta_context_validator.rules import validate_metric


FUSION_INLINE = """
models:
  - name: mart_orders__daily_metrics
    description: "Daily order outcomes by channel."
    config:
      meta:
        context:
          purpose: "Daily order outcomes"
          owner: "Commerce Analytics"
        expectations:
          seasonality: "Peaks in Q4"
        decisions:
          business_rules:
            - "Refunds are excluded from order counts."
        last_validated: "2026-08-21"
    semantic_model:
      enabled: true
      name: orders_daily_metrics
    agg_time_dimension: order_date
    derived_semantics:
      entities:
        - name: orders_daily_metrics
          type: primary
          expr: order_date
    metrics:
      - name: order_count
        type: simple
        config:
          meta:
            context:
              business_question: "How many orders did we take?"
            expectations:
              healthy_range: [1000, 5000]
      - name: order_amount
        type: simple
        config:
          meta:
            context:
              purpose: "Gross order value"
"""

LEGACY = """
models:
  - name: mart_orders__daily_metrics
    semantic_model:
      meta:
        context:
          owner: "Commerce Analytics"
        last_validated: "2026-08-21"
      metrics:
        - name: order_count
          meta:
            context:
              purpose: "Order volume"
"""


def _by_name(pairs):
    return {name: meta for name, meta in pairs}


def test_fusion_inline_metrics_are_found():
    metrics = _extract_metrics(yaml.safe_load(FUSION_INLINE))
    assert sorted(name for name, _ in metrics) == ["order_amount", "order_count"]


def test_model_level_card_merges_into_each_fusion_metric():
    metrics = _by_name(_extract_metrics(yaml.safe_load(FUSION_INLINE)))
    for name in ("order_count", "order_amount"):
        assert metrics[name]["context"]["owner"] == "Commerce Analytics"
        assert metrics[name]["decisions"]["business_rules"]
        assert metrics[name]["last_validated"] == "2026-08-21"


def test_metric_level_wins_over_model_level():
    metrics = _by_name(_extract_metrics(yaml.safe_load(FUSION_INLINE)))
    # order_amount overrides the model-level purpose; order_count inherits it.
    assert metrics["order_amount"]["context"]["purpose"] == "Gross order value"
    assert metrics["order_count"]["context"]["purpose"] == "Daily order outcomes"


def test_legacy_shape_still_extracted():
    metrics = _by_name(_extract_metrics(yaml.safe_load(LEGACY)))
    assert metrics["order_count"]["context"]["purpose"] == "Order volume"
    assert metrics["order_count"]["context"]["owner"] == "Commerce Analytics"
    assert metrics["order_count"]["last_validated"] == "2026-08-21"


def test_same_metric_in_both_locations_resolves_to_the_inline_one():
    """dbt compiles the inline declaration, so that is the one we validate."""
    doc = yaml.safe_load(FUSION_INLINE)
    doc["models"][0]["semantic_model"]["metrics"] = [
        {"name": "order_count", "meta": {"context": {"purpose": "legacy copy"}}}
    ]
    metrics = _extract_metrics(doc)
    assert [n for n, _ in metrics].count("order_count") == 1
    # The inline card inherits the model-level purpose; the legacy copy would
    # have overridden it.
    assert _by_name(metrics)["order_count"]["context"]["purpose"] == "Daily order outcomes"


def test_unnamed_metrics_are_not_deduped():
    """Collapsing them would silently drop every metric after the first."""
    doc = yaml.safe_load("""
models:
  - name: m
    metrics:
      - config: {meta: {context: {purpose: first}}}
      - config: {meta: {context: {purpose: second}}}
""")
    metrics = _extract_metrics(doc)
    assert [m["context"]["purpose"] for _, m in metrics] == ["first", "second"]


def test_unparseable_file_exits_nonzero(tmp_path):
    """A file we could not read is not a file that passed."""
    broken = tmp_path / "broken.yml"
    broken.write_text("models:\n  - name: m\n    config:\n      meta: [unclosed\n")
    result = CliRunner().invoke(main, ["validate", str(broken)])
    assert result.exit_code != 0


def test_top_level_metric_reads_config_meta():
    doc = yaml.safe_load("""
metrics:
  - name: refund_rate
    config:
      meta:
        context:
          purpose: "Share of orders refunded"
""")
    assert _by_name(_extract_metrics(doc))["refund_rate"]["context"]["purpose"]


def test_explicit_null_layer_does_not_crash():
    doc = yaml.safe_load(FUSION_INLINE)
    doc["models"][0]["metrics"][0]["config"]["meta"]["expectations"] = None
    metrics = _by_name(_extract_metrics(doc))
    # Model-level expectations survive; the null metric layer contributes nothing.
    assert metrics["order_count"]["expectations"] == {"seasonality": "Peaks in Q4"}


def test_false_confidence_fires_on_fusion_shape():
    """The check must reach Fusion metrics — thresholds without business rules."""
    doc = yaml.safe_load(FUSION_INLINE)
    del doc["models"][0]["config"]["meta"]["decisions"]
    metrics = _by_name(_extract_metrics(doc))
    result = validate_metric("order_count", metrics["order_count"])
    assert result.has_false_confidence_risk
