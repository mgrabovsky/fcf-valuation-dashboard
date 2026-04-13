from __future__ import annotations

import io
import zipfile

import polars as pl

from ahp_pipeline.sources.bea import parse_bea_response
from ahp_pipeline.sources.fed_z1 import extract_required_tables, parse_release_quarter


def test_parse_bea_response_keeps_quarterly_rows() -> None:
    payload = {
        "BEAAPI": {
            "Results": {
                "Data": [
                    {"TimePeriod": "2024Q1", "LineNumber": "1", "DataValue": "100.0"},
                    {"TimePeriod": "2024Q1", "LineNumber": "2", "DataValue": "56.0"},
                    {"TimePeriod": "2024", "LineNumber": "1", "DataValue": "999.0"},
                ]
            }
        }
    }
    frame = parse_bea_response(payload)
    assert frame.to_dicts() == [
        {"period": "2024Q1", "line_code": "1", "value": 100.0},
        {"period": "2024Q1", "line_code": "2", "value": 56.0},
    ]


def test_extract_required_tables_reads_bundle() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("Z1_2025Q4_B.1.csv", "period,market_equity_nfc\n2024Q1,250.0\n")
        archive.writestr("Z1_2025Q4_L.4.csv", "period,capital_replacement_cost\n2024Q1,302.0\n")
    tables, release_quarter = extract_required_tables(buffer.getvalue())
    assert release_quarter == "2025Q4"
    assert set(tables) == {"B.1", "L.4"}
    assert isinstance(tables["B.1"], pl.DataFrame)


def test_parse_release_quarter() -> None:
    assert parse_release_quarter("Z1_2025Q4_B.1.csv") == "2025Q4"
    assert parse_release_quarter("no-quarter-here") is None
