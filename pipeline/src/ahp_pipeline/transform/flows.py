"""Quarterly flow reconstruction from BEA NIPA data."""

from __future__ import annotations

import polars as pl

FLOW_LINE_CODES: dict[str, str] = {
    "gva": "1",
    "labor_compensation": "2",
    "taxes_total": "3",
    "gross_investment": "4",
    "cfc": "5",
}


def compute_flows(
    frame: pl.DataFrame, line_codes: dict[str, str] | None = None
) -> pl.DataFrame:
    """Pivot normalized BEA rows into the quarterly flow panel used downstream."""
    codes = line_codes or FLOW_LINE_CODES
    pivoted = frame.pivot(on="line_code", index="period", values="value").sort("period")
    selected = pivoted.select(
        pl.col("period"),
        pl.col(codes["gva"]).alias("gva"),
        pl.col(codes["labor_compensation"]).alias("labor_compensation"),
        pl.col(codes["taxes_total"]).alias("taxes_total"),
        pl.col(codes["gross_investment"]).alias("gross_investment"),
        pl.col(codes["cfc"]).alias("cfc"),
    )
    return selected.with_columns(
        (pl.col("gross_investment") - pl.col("cfc")).round(12).alias("net_investment"),
        (
            pl.col("gva")
            - pl.col("labor_compensation")
            - pl.col("taxes_total")
            - pl.col("gross_investment")
        )
        .round(12)
        .alias("fcf"),
    ).with_columns(
        (pl.col("fcf") + pl.col("net_investment")).round(12).alias("earnings")
    )
