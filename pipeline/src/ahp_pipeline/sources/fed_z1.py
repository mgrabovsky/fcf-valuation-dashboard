"""Federal Reserve Z.1 bulk download helpers."""

from __future__ import annotations

import io
import re
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx
import polars as pl

from ahp_pipeline.config import FED_Z1_RELEASE_PAGE_URL, cache_path

RELEASE_PATTERN = re.compile(r"(20[0-9]{2})Q([1-4])", re.IGNORECASE)
TABLE_PATTERN = re.compile(r"(B\.1|L\.4|L\.224|S\.5|S\.6)", re.IGNORECASE)
CSV_URL_PATTERN = re.compile(
    r'href="(?P<path>/releases/z1/\d{8}/z1_csv_files\.zip)"',
    re.IGNORECASE,
)
PAGE_RELEASE_PATTERN = re.compile(
    (
        r"Release Date:\s*(?P<date>[A-Za-z]+\s+\d{1,2},\s+\d{4})\s*"
        r"\((?P<quarter>\d{4}:Q[1-4]) Release\)"
    ),
    re.IGNORECASE,
)


@dataclass(frozen=True)
class FedZ1NormalizedData:
    enterprise_value_components: pl.DataFrame
    capital: pl.DataFrame
    gross_investment: pl.DataFrame


@dataclass(frozen=True)
class FedZ1ReleaseMetadata:
    csv_url: str
    vintage: str
    release_quarter: str


@dataclass(frozen=True)
class FedZ1SourceResult:
    data: FedZ1NormalizedData
    vintage: str
    release_quarter: str
    url: str


def parse_release_quarter(name: str) -> str | None:
    """Extract a release quarter from a filename or metadata string."""
    match = RELEASE_PATTERN.search(name)
    if match:
        return f"{match.group(1)}Q{match.group(2)}"
    return None


def parse_release_metadata(html: str) -> FedZ1ReleaseMetadata:
    """Extract the current CSV ZIP URL and release metadata from the Z.1 landing page."""
    csv_match = CSV_URL_PATTERN.search(html)
    if csv_match is None:
        message = "Could not find the current Z.1 CSV ZIP link on the release page."
        raise ValueError(message)

    release_match = PAGE_RELEASE_PATTERN.search(html)
    if release_match is None:
        message = "Could not find the current Z.1 release date and quarter on the release page."
        raise ValueError(message)

    release_date = (
        datetime.strptime(release_match.group("date"), "%B %d, %Y").date().isoformat()
    )
    release_quarter = release_match.group("quarter").replace(":", "")
    return FedZ1ReleaseMetadata(
        csv_url=str(httpx.URL(FED_Z1_RELEASE_PAGE_URL).join(csv_match.group("path"))),
        vintage=release_date,
        release_quarter=release_quarter,
    )


def parse_table_csv(content: bytes) -> pl.DataFrame:
    """Parse a single CSV payload from the Z.1 bundle."""
    return pl.read_csv(io.BytesIO(content), null_values=["", "NA", "ND"])


def _normalize_periods(frame: pl.DataFrame) -> pl.DataFrame:
    if "date" not in frame.columns:
        message = "The Z.1 CSV is missing its date column."
        raise ValueError(message)
    return frame.with_columns(pl.col("date").str.replace(":", "").alias("period"))


def _require_columns(
    frame: pl.DataFrame, columns: tuple[str, ...], table_name: str
) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        message = f"{table_name} is missing required columns: {', '.join(missing)}"
        raise ValueError(message)


def _select_series(
    frame: pl.DataFrame,
    *,
    table_name: str,
    series: Mapping[str, str],
) -> pl.DataFrame:
    required = tuple(series.values())
    _require_columns(frame, required, table_name)
    return frame.select(
        pl.col("period"),
        *(
            pl.col(source_column).cast(pl.Float64).alias(target_column)
            for target_column, source_column in series.items()
        ),
    )


def extract_required_data(bundle: bytes) -> tuple[FedZ1NormalizedData, str]:
    """Extract the normalized quarterly Z.1 inputs required by the v1 pipeline."""
    release_quarter: str | None = None
    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
        for name in archive.namelist():
            if release_quarter is None:
                release_quarter = parse_release_quarter(name)

        b103 = _normalize_periods(parse_table_csv(archive.read("csv/b103.csv")))
        l224 = _normalize_periods(parse_table_csv(archive.read("csv/l224.csv")))
        l4s = _normalize_periods(parse_table_csv(archive.read("csv/l4s.csv")))
        all_sectors_flows_q = _normalize_periods(
            parse_table_csv(archive.read("csv/all_sectors_flows_q.csv"))
        )

    # Live Z.1 CSVs expose a clean nonfinancial-corporate balance sheet in B.103.
    # L.224 splits public and closely held NFC equity, which lets the EV transform
    # keep the closely held component explicit instead of hiding it in total equity.
    # The nearest financial-business equity line in the bulk CSV is "domestic
    # financial sectors" (`LM793164105.Q`), which is broader than the BEA
    # corporate-business scope used elsewhere in the pipeline, so v1 leaves the
    # financial-business market-equity add-on at zero rather than overstate EV.
    enterprise_value_components = (
        _select_series(
            l224,
            table_name="L.224",
            series={
                "market_equity_nfc": "LM103164115.Q",
                "closely_held_imputation": "LM103164125.Q",
            },
        )
        .join(
            _select_series(
                b103,
                table_name="B.103",
                series={
                    "liabilities": "FL104190005.Q",
                    "financial_assets": "FL104090005.Q",
                    "fdi_inward_equity": "LM103192105.Q",
                    "fdi_outward_equity": "LM103092105.Q",
                },
            ),
            on="period",
            how="inner",
        )
        .with_columns(pl.lit(0.0).alias("market_equity_fb"))
    )

    capital = _select_series(
        l4s,
        table_name="L.4.s",
        series={"capital_replacement_cost": "FL105015085.Q"},
    )
    # The live quarterly matrix carries the broad nonfinancial-business fixed-
    # investment aggregate (`FA145013005`) even when the narrower table-specific
    # CSVs only expose NFC detail. That broader line keeps the v1 flow panel on
    # the paper's historical sanity range while remaining a published quarterly
    # Z.1 series, so it is the current gross-investment input.
    gross_investment = _select_series(
        all_sectors_flows_q,
        table_name="all_sectors_flows_q",
        series={"gross_investment": "FA145013005"},
    )

    if release_quarter is None:
        release_quarter = f"{datetime.now(UTC).year}Q1"
    return (
        FedZ1NormalizedData(
            enterprise_value_components=enterprise_value_components,
            capital=capital,
            gross_investment=gross_investment,
        ),
        release_quarter,
    )


class FedZ1Client:
    """Downloader and parser for the Z.1 bulk ZIP."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(timeout=60.0)

    def fetch_release_metadata(self) -> FedZ1ReleaseMetadata:
        """Fetch the release landing page and extract the current CSV ZIP metadata."""
        response = self._client.get(FED_Z1_RELEASE_PAGE_URL)
        response.raise_for_status()
        return parse_release_metadata(response.text)

    def fetch_bundle(self) -> FedZ1SourceResult:
        """Fetch the bundle, cache it, and return parsed tables."""
        metadata = self.fetch_release_metadata()
        cache_file = cache_path("fed-z1", metadata.csv_url, "zip")
        if cache_file.exists():
            bundle = cache_file.read_bytes()
        else:
            response = self._client.get(metadata.csv_url)
            response.raise_for_status()
            bundle = response.content
            Path(cache_file).write_bytes(bundle)
        data, release_quarter = extract_required_data(bundle)
        return FedZ1SourceResult(
            data=data,
            vintage=metadata.vintage,
            release_quarter=release_quarter or metadata.release_quarter,
            url=metadata.csv_url,
        )
