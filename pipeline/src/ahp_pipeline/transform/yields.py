"""Derived valuation ratios."""

from __future__ import annotations

import polars as pl


def compute_ratios(frame: pl.DataFrame) -> pl.DataFrame:
    """Compute all derived ratio series required by schema v1."""
    return frame.with_columns(
        (pl.col("fcf") / pl.col("enterprise_value")).alias("fcf_yield"),
        (pl.col("earnings") / pl.col("enterprise_value")).alias("earnings_yield"),
        (pl.col("enterprise_value") / pl.col("gva")).alias("ev_gva"),
        (pl.col("capital_replacement_cost") / pl.col("gva")).alias("k_gva"),
        (pl.col("fcf") / pl.col("gva")).alias("fcf_gva"),
        (pl.col("labor_compensation") / pl.col("gva")).alias("labor_share"),
        (pl.col("net_investment") / pl.col("enterprise_value")).alias("net_inv_v"),
        (pl.col("net_investment") / pl.col("capital_replacement_cost")).alias(
            "net_inv_k"
        ),
        (pl.col("capital_replacement_cost") / pl.col("enterprise_value")).alias("k_v"),
        (pl.col("fcf") / pl.col("earnings")).alias("payout_ratio"),
    )
