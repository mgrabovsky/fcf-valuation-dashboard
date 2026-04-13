"""Federal Reserve Z.1 bulk download helpers."""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx
import polars as pl

from ahp_pipeline.config import FED_Z1_ZIP_URL, cache_path

RELEASE_PATTERN = re.compile(r"(20[0-9]{2})Q([1-4])", re.IGNORECASE)
TABLE_PATTERN = re.compile(r"(B\.1|L\.4|L\.224|S\.5|S\.6)", re.IGNORECASE)


@dataclass(frozen=True)
class FedZ1SourceResult:
    tables: dict[str, pl.DataFrame]
    vintage: str
    release_quarter: str
    url: str


def parse_release_quarter(name: str) -> str | None:
    """Extract a release quarter from a filename or metadata string."""
    match = RELEASE_PATTERN.search(name)
    if match:
        return f"{match.group(1)}Q{match.group(2)}"
    return None


def parse_table_csv(content: bytes) -> pl.DataFrame:
    """Parse a single CSV payload from the Z.1 bundle."""
    return pl.read_csv(io.BytesIO(content))


def extract_required_tables(bundle: bytes) -> tuple[dict[str, pl.DataFrame], str]:
    """Extract the Z.1 tables required by the v1 pipeline."""
    tables: dict[str, pl.DataFrame] = {}
    release_quarter: str | None = None
    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
        for name in archive.namelist():
            if release_quarter is None:
                release_quarter = parse_release_quarter(name)
            match = TABLE_PATTERN.search(name)
            if not match:
                continue
            table_name = match.group(1).upper()
            with archive.open(name) as member:
                tables[table_name] = parse_table_csv(member.read())
    if release_quarter is None:
        release_quarter = f"{datetime.now(UTC).year}Q1"
    return tables, release_quarter


class FedZ1Client:
    """Downloader and parser for the Z.1 bulk ZIP."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(timeout=60.0)

    def fetch_bundle(self) -> FedZ1SourceResult:
        """Fetch the bundle, cache it, and return parsed tables."""
        cache_file = cache_path("fed-z1", FED_Z1_ZIP_URL, "zip")
        if cache_file.exists():
            bundle = cache_file.read_bytes()
        else:
            response = self._client.get(FED_Z1_ZIP_URL)
            response.raise_for_status()
            bundle = response.content
            Path(cache_file).write_bytes(bundle)
        tables, release_quarter = extract_required_tables(bundle)
        return FedZ1SourceResult(
            tables=tables,
            vintage=datetime.now(UTC).date().isoformat(),
            release_quarter=release_quarter,
            url=FED_Z1_ZIP_URL,
        )
