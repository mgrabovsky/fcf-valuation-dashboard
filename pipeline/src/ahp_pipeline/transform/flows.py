"""Quarterly flow reconstruction from BEA NIPA data."""

from __future__ import annotations

import polars as pl

type FlowLineCode = str | tuple[str, ...]


FLOW_LINE_CODES: dict[str, FlowLineCode] = {
    "gva": "1",
    "labor_compensation": "4",
    "taxes_total": ("7", "10", "12"),
    "cfc": "2",
}


def _line_code_expr(line_code: FlowLineCode) -> pl.Expr:
    if isinstance(line_code, str):
        return pl.col(line_code)
    return sum((pl.col(code) for code in line_code), pl.lit(0.0))


def compute_flows(
    frame: pl.DataFrame, line_codes: dict[str, FlowLineCode] | None = None
) -> pl.DataFrame:
    """Pivot normalized BEA rows into the quarterly flow panel used downstream."""
    codes = line_codes or FLOW_LINE_CODES
    pivoted = frame.pivot(on="line_code", index="period", values="value").sort("period")
    return pivoted.select(
        pl.col("period"),
        _line_code_expr(codes["gva"]).alias("gva"),
        _line_code_expr(codes["labor_compensation"]).alias("labor_compensation"),
        _line_code_expr(codes["taxes_total"]).alias("taxes_total"),
        _line_code_expr(codes["cfc"]).alias("cfc"),
    )


def finalize_flows(frame: pl.DataFrame) -> pl.DataFrame:
    """Derive investment and cash-flow series once gross investment has been joined."""
    return frame.with_columns(
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
