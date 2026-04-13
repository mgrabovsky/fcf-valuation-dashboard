"""BEA NIPA Table 1.14 source adapter."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx
import polars as pl

from ahp_pipeline.config import BEA_API_URL, BEA_TABLE_NAME, cache_path

DATE_PATTERN = re.compile(r"(20[0-9]{2}-[0-9]{2}-[0-9]{2})")


@dataclass(frozen=True)
class BeaSourceResult:
    data: pl.DataFrame
    vintage: str
    url: str


def _parse_number(value: str) -> float | None:
    stripped = value.strip()
    if stripped in {"", "(NA)", "NA"}:
        return None
    cleaned = stripped.replace(",", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = f"-{cleaned[1:-1]}"
    return float(cleaned)


def parse_bea_response(payload: dict[str, Any]) -> pl.DataFrame:
    """Convert the BEA JSON payload into a normalized quarterly frame."""
    rows = payload["BEAAPI"]["Results"]["Data"]
    normalized: list[dict[str, object]] = []
    for row in rows:
        period = str(row["TimePeriod"])
        line_code = str(row["LineNumber"])
        value = _parse_number(str(row["DataValue"]))
        if not period.endswith(("Q1", "Q2", "Q3", "Q4")):
            continue
        normalized.append({"period": period, "line_code": line_code, "value": value})
    return pl.DataFrame(normalized).sort(["period", "line_code"])


def extract_bea_vintage(payload: dict[str, Any]) -> str:
    """Best-effort extraction of a BEA release date from the payload metadata."""
    serialized = json.dumps(payload)
    match = DATE_PATTERN.search(serialized)
    if match:
        return match.group(1)
    return datetime.now(UTC).date().isoformat()


class BeaClient:
    """Small sync client for the BEA REST API."""

    def __init__(self, api_key: str, client: httpx.Client | None = None) -> None:
        self._api_key = api_key
        self._client = client or httpx.Client(timeout=30.0)

    def fetch_table(self, table_name: str = BEA_TABLE_NAME) -> BeaSourceResult:
        """Fetch and parse quarterly NIPA table data."""
        params = {
            "UserID": self._api_key,
            "method": "GetData",
            "datasetname": "NIPA",
            "TableName": table_name,
            "Frequency": "Q",
            "Year": "X",
            "ResultFormat": "JSON",
        }
        cache_key = json.dumps(params, sort_keys=True)
        cache_file = cache_path("bea", cache_key, "json")
        if cache_file.exists():
            payload = json.loads(cache_file.read_text(encoding="utf-8"))
        else:
            response = self._client.get(BEA_API_URL, params=params)
            response.raise_for_status()
            payload = response.json()
            cache_file.write_text(json.dumps(payload), encoding="utf-8")
        return BeaSourceResult(
            data=parse_bea_response(payload),
            vintage=extract_bea_vintage(payload),
            url=str(httpx.URL(BEA_API_URL, params=params)),
        )
