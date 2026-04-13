"""Enterprise value reconstruction following the AHP methodology.

References:
- https://www.federalreserve.gov/econres/notes/feds-notes/measuring-the-market-value-of-nonfinancial-corporate-business.htm
- https://www.federalreserve.gov/releases/z1/
- https://www.bea.gov/resources/methodologies/nipa-handbook

The live Z.1 normalization layer maps the bundle to these semantic inputs:
- `market_equity_nfc`: L.224 `LM103164115.Q` public NFC corporate equity liability
- `closely_held_imputation`: L.224 `LM103164125.Q` closely held NFC equity liability
- `liabilities`: B.103 `FL104190005.Q` total NFC liabilities
- `financial_assets`: B.103 `FL104090005.Q` total NFC financial assets
- `fdi_inward_equity`: B.103 `LM103192105.Q` foreign direct investment in U.S.
- `fdi_outward_equity`: B.103 `LM103092105.Q` U.S. direct investment abroad
"""

from __future__ import annotations

import polars as pl

# The closely-held and FDI adjustments are the highest-risk part of the pipeline.
# Keep the input column names explicit so line mapping changes are visible in code review.
EV_COMPONENT_COLUMNS: dict[str, str] = {
    "market_equity_nfc": "market_equity_nfc",
    "market_equity_fb": "market_equity_fb",
    "liabilities": "liabilities",
    "financial_assets": "financial_assets",
    "closely_held_imputation": "closely_held_imputation",
    "fdi_inward_equity": "fdi_inward_equity",
    "fdi_outward_equity": "fdi_outward_equity",
}


def compute_enterprise_value(
    frame: pl.DataFrame, columns: dict[str, str] | None = None
) -> pl.DataFrame:
    """Compute enterprise value from a normalized quarterly component frame."""
    names = columns or EV_COMPONENT_COLUMNS
    return frame.select(
        pl.col("period"),
        (
            pl.col(names["market_equity_nfc"])
            + pl.col(names["market_equity_fb"])
            + pl.col(names["liabilities"])
            - pl.col(names["financial_assets"])
            + pl.col(names["closely_held_imputation"])
            + pl.col(names["fdi_inward_equity"])
            - pl.col(names["fdi_outward_equity"])
        ).alias("enterprise_value"),
    )
