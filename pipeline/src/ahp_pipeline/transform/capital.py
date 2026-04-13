"""Capital stock transformations."""

from __future__ import annotations

import polars as pl


def compute_capital(frame: pl.DataFrame) -> pl.DataFrame:
    """Keep the capital replacement cost series in the normalized quarterly panel."""
    return frame.select(pl.col("period"), pl.col("capital_replacement_cost"))
