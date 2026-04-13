"""Validation and accounting identities for the dataset artifact."""

from __future__ import annotations

import math
from collections.abc import Mapping

from ahp_pipeline.models import Dataset

RATIO_TOLERANCE = 1e-6
LEVEL_TOLERANCE = 1e-3


def _assert_close(left: float, right: float, tolerance: float, label: str) -> None:
    if not math.isclose(left, right, rel_tol=0.0, abs_tol=tolerance):
        message = f"{label} failed: {left} != {right} within {tolerance}"
        raise ValueError(message)


def _assert_no_nan(values: list[float | None], label: str) -> None:
    for value in values:
        if value is not None and math.isnan(value):
            message = f"{label} contains NaN values."
            raise ValueError(message)


def _series_map(dataset: Dataset) -> Mapping[str, list[float | None]]:
    return {key: value["values"] for key, value in dataset.series.model_dump().items()}


def _require_number(value: float | int | None, label: str, index: int) -> float:
    if value is None:
        message = f"{label} contains a null value at index {index}."
        raise ValueError(message)
    return float(value)


def validate_dataset(dataset: Dataset) -> None:
    """Run the hard validation suite on the dataset artifact."""
    series = _series_map(dataset)
    periods_len = len(dataset.periods)
    for key, values in series.items():
        if len(values) != periods_len:
            message = f"{key} length {len(values)} does not match periods length {periods_len}."
            raise ValueError(message)
        _assert_no_nan(values, key)

    numeric_series = {
        key: [value for value in values if value is not None]
        for key, values in series.items()
    }

    for index in range(periods_len):
        gva = _require_number(series["gva"][index], "gva", index)
        labor = _require_number(
            series["labor_compensation"][index], "labor_compensation", index
        )
        taxes = _require_number(series["taxes_total"][index], "taxes_total", index)
        gross = _require_number(
            series["gross_investment"][index], "gross_investment", index
        )
        fcf = _require_number(series["fcf"][index], "fcf", index)
        earnings = _require_number(series["earnings"][index], "earnings", index)
        net_investment = _require_number(
            series["net_investment"][index], "net_investment", index
        )
        net_inv_v = _require_number(series["net_inv_v"][index], "net_inv_v", index)
        net_inv_k = _require_number(series["net_inv_k"][index], "net_inv_k", index)
        k_v = _require_number(series["k_v"][index], "k_v", index)

        _assert_close(gva, labor + taxes + gross + fcf, LEVEL_TOLERANCE, "gva identity")
        _assert_close(
            earnings - fcf, net_investment, LEVEL_TOLERANCE, "earnings identity"
        )
        _assert_close(net_inv_v, net_inv_k * k_v, RATIO_TOLERANCE, "equation 1")

    fcf_mean = sum(numeric_series["fcf_yield"]) / len(numeric_series["fcf_yield"])
    if not 0.03 <= fcf_mean <= 0.04:
        message = f"fcf_yield mean {fcf_mean} is outside the allowed sanity range."
        raise ValueError(message)
