"""Dataset serialization and schema validation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from statistics import mean, pstdev
from typing import Any

import jsonschema
import polars as pl

from ahp_pipeline.config import DATASET_PATH, MANIFEST_PATH, SCHEMA_PATH
from ahp_pipeline.manifest import build_manifest
from ahp_pipeline.models import (
    Dataset,
    DatasetSeries,
    DatasetStats,
    Series,
    Sources,
    Stats,
)
from ahp_pipeline.validate import validate_dataset

LEVEL_SERIES = [
    "gva",
    "labor_compensation",
    "taxes_total",
    "gross_investment",
    "cfc",
    "net_investment",
    "fcf",
    "earnings",
    "enterprise_value",
    "capital_replacement_cost",
]

RATIO_SERIES = [
    "fcf_yield",
    "earnings_yield",
    "ev_gva",
    "k_gva",
    "fcf_gva",
    "labor_share",
    "net_inv_v",
    "net_inv_k",
    "k_v",
    "payout_ratio",
]

SERIES_META: dict[str, tuple[str, str]] = {
    "gva": ("Corporate gross value added", "Corporate gross value added."),
    "labor_compensation": (
        "Labor compensation",
        "Compensation of employees for the corporate sector.",
    ),
    "taxes_total": (
        "Total taxes",
        "Indirect business taxes, transfers, and corporate taxes.",
    ),
    "gross_investment": ("Gross investment", "Corporate gross fixed investment."),
    "cfc": ("Consumption of fixed capital", "Corporate consumption of fixed capital."),
    "net_investment": (
        "Net investment",
        "Gross investment minus consumption of fixed capital.",
    ),
    "fcf": (
        "Free cash flow",
        "Gross value added less labor, taxes, and gross investment.",
    ),
    "earnings": ("Earnings", "Free cash flow plus net investment."),
    "enterprise_value": (
        "Enterprise value",
        "Corporate enterprise value following the AHP definition.",
    ),
    "capital_replacement_cost": (
        "Capital replacement cost",
        "Current-cost replacement value of fixed corporate assets.",
    ),
    "fcf_yield": (
        "Free cash flow yield",
        "Free cash flow divided by enterprise value.",
    ),
    "earnings_yield": ("Earnings yield", "Earnings divided by enterprise value."),
    "ev_gva": ("EV / GVA", "Enterprise value divided by gross value added."),
    "k_gva": ("K / GVA", "Capital replacement cost divided by gross value added."),
    "fcf_gva": ("FCF / GVA", "Free cash flow divided by gross value added."),
    "labor_share": ("Labor share", "Labor compensation divided by gross value added."),
    "net_inv_v": ("Net investment / V", "Net investment divided by enterprise value."),
    "net_inv_k": (
        "Net investment / K",
        "Net investment divided by capital replacement cost.",
    ),
    "k_v": ("K / V", "Capital replacement cost divided by enterprise value."),
    "payout_ratio": ("Payout ratio", "Free cash flow divided by earnings."),
}


def _stats(values: list[float | None]) -> Stats:
    clean = [value for value in values if value is not None]
    if not clean:
        message = "Cannot compute stats for an empty series."
        raise ValueError(message)
    return Stats(mean=mean(clean), std=pstdev(clean), min=min(clean), max=max(clean))


def _frame_values(frame: pl.DataFrame, column: str) -> list[float | None]:
    return frame.get_column(column).to_list()


def build_dataset(
    frame: pl.DataFrame, sources: Sources, generated_at: str | None = None
) -> Dataset:
    """Build the pydantic dataset model from a quarterly panel."""
    timestamp = generated_at or (
        datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    payload: dict[str, Series] = {}
    for key in [*LEVEL_SERIES, *RATIO_SERIES]:
        label, description = SERIES_META[key]
        unit = "level" if key in LEVEL_SERIES else "ratio"
        payload[key] = Series(
            label=label,
            description=description,
            unit=unit,
            values=_frame_values(frame, key),
        )
    ratio_stats = {key: _stats(payload[key].values) for key in RATIO_SERIES}
    dataset = Dataset(
        schema_version="1.0.0",
        generated_at=timestamp,
        sources=sources,
        frequency="quarterly",
        periods=frame.get_column("period").to_list(),
        series=DatasetSeries(**payload),
        stats=DatasetStats(**ratio_stats),
    )
    validate_dataset(dataset)
    return dataset


def validate_against_schema(payload: dict[str, Any]) -> None:
    """Validate a raw dataset payload against the shared JSON Schema."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(payload)


def write_dataset(frame: pl.DataFrame, sources: Sources) -> Dataset:
    """Serialize the dataset and manifest to disk."""
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataset = build_dataset(frame, sources)
    payload = dataset.model_dump(mode="json")
    validate_against_schema(payload)
    DATASET_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    manifest = build_manifest(
        schema_version=dataset.schema_version,
        generated_at=dataset.generated_at,
        dataset_path=DATASET_PATH,
        sources=sources,
    )
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    return dataset
