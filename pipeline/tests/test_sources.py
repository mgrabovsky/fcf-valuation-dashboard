from __future__ import annotations

import io
import zipfile

import polars as pl

from ahp_pipeline.sources.bea import parse_bea_response
from ahp_pipeline.sources.fed_z1 import (
    extract_required_data,
    parse_release_metadata,
    parse_release_quarter,
)


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


def test_extract_required_data_reads_bundle() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("metadata/Z1_2025Q4_release.txt", "placeholder\n")
        archive.writestr(
            "csv/b103.csv",
            (
                "date,FL104190005.Q,FL104090005.Q,LM103192105.Q,LM103092105.Q\n"
                "2024:Q1,520.0,240.0,40.0,10.0\n"
            ),
        )
        archive.writestr(
            "csv/l224.csv",
            ("date,LM103164115.Q,LM103164125.Q\n2024:Q1,250.0,30.0\n"),
        )
        archive.writestr("csv/l4s.csv", "date,FL105015085.Q\n2024:Q1,302.0\n")
        archive.writestr(
            "csv/all_sectors_flows_q.csv",
            "date,FA145013005\n2024:Q1,12.0\n",
        )
    data, release_quarter = extract_required_data(buffer.getvalue())
    assert release_quarter == "2025Q4"
    assert isinstance(data.enterprise_value_components, pl.DataFrame)
    assert data.enterprise_value_components.row(0, named=True) == {
        "period": "2024Q1",
        "market_equity_nfc": 250.0,
        "closely_held_imputation": 30.0,
        "liabilities": 520.0,
        "financial_assets": 240.0,
        "fdi_inward_equity": 40.0,
        "fdi_outward_equity": 10.0,
        "market_equity_fb": 0.0,
    }
    assert data.capital.row(0, named=True) == {
        "period": "2024Q1",
        "capital_replacement_cost": 302.0,
    }
    assert data.gross_investment.row(0, named=True) == {
        "period": "2024Q1",
        "gross_investment": 12.0,
    }


def test_parse_release_quarter() -> None:
    assert parse_release_quarter("Z1_2025Q4_B.1.csv") == "2025Q4"
    assert parse_release_quarter("no-quarter-here") is None


def test_parse_release_metadata() -> None:
    html = """
    <html>
      <body>
        <p>Release Date: March 19, 2026 (2025:Q4 Release)</p>
        <a href="/releases/z1/20260319/z1_csv_files.zip">CSV</a>
      </body>
    </html>
    """
    metadata = parse_release_metadata(html)
    assert metadata.vintage == "2026-03-19"
    assert metadata.release_quarter == "2025Q4"
    assert (
        metadata.csv_url
        == "https://www.federalreserve.gov/releases/z1/20260319/z1_csv_files.zip"
    )
