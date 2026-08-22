"""CLI for dbt-meta-context-validator."""

import json
import sys
from pathlib import Path

import click
import yaml

from .rules import validate_metric


def _find_yaml_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.rglob("*.yml")) + sorted(path.rglob("*.yaml"))


LAYERS = ("context", "expectations", "investigation", "relationships", "decisions")


def _meta_of(node: dict) -> dict:
    """Read a node's meta block from whichever location the project writes it.

    dbt Fusion's inline spec nests it under `config.meta` (for models and for
    `models[].metrics[]` alike); the legacy semantic-model spec writes a bare
    `meta`. Both shapes are in the wild, and looking in only one reports
    "0 metrics, exit 0" on a fully populated file — worse than an error.

    A populated `config.meta` wins; a bare `meta` is the fallback. An empty
    `config.meta` is not a statement, so it does not suppress a populated bare
    `meta`. If both are populated the bare one is NOT merged in — dbt compiles
    one of them, not their union, and silently validating a card the warehouse
    never sees would be its own false clean.
    """
    if not isinstance(node, dict):
        return {}
    config = node.get("config") or {}
    config_meta = config.get("meta") if isinstance(config, dict) else None
    if isinstance(config_meta, dict) and config_meta:
        return config_meta
    meta = node.get("meta")
    return meta if isinstance(meta, dict) else {}


def _model_metrics(model: dict) -> list[dict]:
    """Metric nodes of a model, from both the inline and legacy locations.

    Named metrics are deduped, inline-first: a name declared in both places is
    one metric, and the inline (Fusion) declaration is the one dbt compiles
    today, so it is the one we validate. dbt itself rejects the duplicate at
    parse time — this only decides what the validator reports in the meantime.

    Unnamed metrics are never deduped. They all report as "unknown", and
    collapsing them would silently drop every metric after the first.
    """
    semantic = model.get("semantic_model")
    sources = (
        model.get("metrics"),
        (semantic.get("metrics") if isinstance(semantic, dict) else None),
    )
    metrics, seen = [], set()
    for source in sources:
        for metric in source or []:
            if not isinstance(metric, dict):
                continue
            name = metric.get("name")
            if name is not None:
                if name in seen:
                    continue
                seen.add(name)
            metrics.append(metric)
    return metrics


def _merge_meta(model_level: dict, metric_meta: dict) -> dict:
    """Merge model-level meta under metric-level meta (metric wins on conflict).

    `or {}` throughout — a layer set to explicit null must not crash the walk.
    """
    merged = {}
    for layer in LAYERS:
        model_layer = model_level.get(layer) or {}
        metric_layer = metric_meta.get(layer) or {}
        merged[layer] = {**model_layer, **metric_layer}
    if metric_meta.get("last_validated"):
        merged["last_validated"] = metric_meta["last_validated"]
    elif model_level.get("last_validated"):
        merged["last_validated"] = model_level["last_validated"]
    return merged


def _extract_metrics(yaml_content: dict) -> list[tuple[str, dict]]:
    """Extract (metric_name, meta_dict) pairs from a parsed YAML file."""
    results = []
    for model in yaml_content.get("models") or []:
        if not isinstance(model, dict):
            continue
        # The model-level card: legacy puts it on `semantic_model.meta`,
        # Fusion on the model's own `config.meta`.
        semantic = model.get("semantic_model")
        model_level_meta = _meta_of(semantic) or _meta_of(model)
        for metric in _model_metrics(model):
            name = metric.get("name", "unknown")
            results.append((name, _merge_meta(model_level_meta, _meta_of(metric))))
    # Also handle top-level metrics blocks
    for metric in yaml_content.get("metrics") or []:
        if not isinstance(metric, dict):
            continue
        results.append((metric.get("name", "unknown"), _meta_of(metric)))
    return results


@click.group()
def main():
    """dbt-meta-context validator."""


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
@click.option("--errors-only", is_flag=True, help="Only show errors and false-confidence risks")
def validate(path: str, output_format: str, errors_only: bool):
    """Validate meta context blocks in dbt semantic model YAML files."""
    target = Path(path)
    yaml_files = _find_yaml_files(target)

    all_results = []
    exit_code = 0

    for yaml_file in yaml_files:
        try:
            content = yaml.safe_load(yaml_file.read_text())
        except yaml.YAMLError as e:
            # A file we could not read is not a file that passed. Reporting
            # "0 metrics" and exiting 0 here would be the same false clean the
            # extractor was fixed to stop producing.
            click.echo(f"Error parsing {yaml_file}: {e}", err=True)
            exit_code = max(exit_code, 1)
            continue

        if not content:
            continue

        metrics = _extract_metrics(content)
        if not metrics:
            continue

        file_results = []
        for metric_name, meta in metrics:
            result = validate_metric(metric_name, meta)
            file_results.append(result)
            if result.errors:
                exit_code = max(exit_code, 1)
            if result.has_false_confidence_risk:
                exit_code = max(exit_code, 2)

        all_results.append({"file": str(yaml_file), "metrics": file_results})

    if output_format == "json":
        output = []
        for file_data in all_results:
            file_json = {"file": file_data["file"], "metrics": []}
            for r in file_data["metrics"]:
                file_json["metrics"].append({
                    "name": r.metric_name,
                    "tier": r.tier,
                    "findings": [
                        {"level": f.level, "rule": f.rule, "message": f.message}
                        for f in r.findings
                    ],
                })
            output.append(file_json)
        click.echo(json.dumps(output, indent=2))
    else:
        for file_data in all_results:
            click.echo(f"\n{file_data['file']}")
            for r in file_data["metrics"]:
                click.echo(f"  metric: {r.metric_name}")
                tier_symbol = {"none": "✗", "bronze": "✓", "silver": "✓", "gold": "✓"}
                tier_label = r.tier.capitalize()
                click.echo(f"    {tier_symbol.get(r.tier, '?')} {tier_label} tier")

                for finding in r.findings:
                    if errors_only and finding.level == "info":
                        continue
                    symbol = {"error": "✗", "warning": "⚠", "info": "·"}.get(finding.level, " ")
                    click.echo(f"    {symbol} {finding.message}")

        # Summary
        total = sum(len(fd["metrics"]) for fd in all_results)
        by_tier = {"none": 0, "bronze": 0, "silver": 0, "gold": 0}
        false_confidence = 0
        for fd in all_results:
            for r in fd["metrics"]:
                by_tier[r.tier] = by_tier.get(r.tier, 0) + 1
                if r.has_false_confidence_risk:
                    false_confidence += 1
        click.echo(
            f"\nSummary: {total} metrics | "
            f"{by_tier['bronze']} Bronze | {by_tier['silver']} Silver | {by_tier['gold']} Gold | "
            f"{by_tier['none']} below Bronze | "
            f"{false_confidence} false-confidence risk"
        )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
