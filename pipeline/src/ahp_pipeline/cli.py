"""Command line interface for the AHP ETL pipeline."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

import polars as pl

from ahp_pipeline.config import DATASET_PATH, MANIFEST_PATH, require_bea_api_key
from ahp_pipeline.manifest import compare_vintages, load_manifest
from ahp_pipeline.models import BeaSource, Dataset, FedSource, Sources
from ahp_pipeline.output import validate_against_schema, write_dataset
from ahp_pipeline.sources.bea import BeaClient
from ahp_pipeline.sources.fed_z1 import FedZ1Client, FedZ1NormalizedData
from ahp_pipeline.transform.capital import compute_capital
from ahp_pipeline.transform.enterprise_value import compute_enterprise_value
from ahp_pipeline.transform.flows import compute_flows, finalize_flows
from ahp_pipeline.transform.yields import compute_ratios
from ahp_pipeline.validate import validate_dataset


def _build_quarterly_panel(
    bea_frame: pl.DataFrame, fed_data: FedZ1NormalizedData
) -> pl.DataFrame:
    flows = compute_flows(bea_frame)
    flows = finalize_flows(
        flows.join(fed_data.gross_investment, on="period", how="inner")
    )
    panel = flows.join(
        compute_enterprise_value(fed_data.enterprise_value_components),
        on="period",
        how="inner",
    )
    panel = panel.join(compute_capital(fed_data.capital), on="period", how="inner")
    return compute_ratios(panel).sort("period")


def run_pipeline() -> int:
    """Execute the full ETL pipeline."""
    bea_client = BeaClient(require_bea_api_key())
    fed_client = FedZ1Client()
    bea = bea_client.fetch_table()
    fed = fed_client.fetch_bundle()
    panel = _build_quarterly_panel(bea.data, fed.data)
    sources = Sources(
        bea_nipa_table_1_14=BeaSource(vintage=bea.vintage, url=bea.url),
        fed_z1=FedSource(
            vintage=fed.vintage,
            release_quarter=fed.release_quarter,
            url=fed.url,
        ),
    )
    write_dataset(panel, sources)
    return 0


def validate_committed_dataset() -> int:
    """Validate the committed artifact against the schema and identity checks."""
    payload = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    validate_against_schema(payload)
    validate_dataset(Dataset.model_validate(payload))
    return 0


def check_vintage() -> int:
    """Probe current source vintages and signal whether a full run should proceed."""
    bea_client = BeaClient(require_bea_api_key())
    fed_client = FedZ1Client()
    bea = bea_client.fetch_table()
    fed = fed_client.fetch_release_metadata()
    existing = load_manifest(MANIFEST_PATH)
    current_sources = Sources(
        bea_nipa_table_1_14=BeaSource(vintage=bea.vintage, url=bea.url),
        fed_z1=FedSource(
            vintage=fed.vintage,
            release_quarter=fed.release_quarter,
            url=fed.csv_url,
        ),
    )
    comparison = compare_vintages(existing, current_sources)
    return 1 if comparison.has_new_vintage else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI."""
    parser = argparse.ArgumentParser(prog="ahp-pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("run")
    subparsers.add_parser("check-vintage")
    subparsers.add_parser("validate")
    args = parser.parse_args(argv)
    match args.command:
        case "run":
            return run_pipeline()
        case "check-vintage":
            return check_vintage()
        case "validate":
            return validate_committed_dataset()
        case _:
            message = f"Unknown command: {args.command}"
            raise ValueError(message)
