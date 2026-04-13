from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def bea_rows() -> pl.DataFrame:
    return pl.read_json(FIXTURES_DIR / "bea_rows.json")


@pytest.fixture
def ev_components() -> pl.DataFrame:
    return pl.read_json(FIXTURES_DIR / "ev_components.json")


@pytest.fixture
def capital_rows() -> pl.DataFrame:
    return pl.read_json(FIXTURES_DIR / "capital_rows.json")


@pytest.fixture
def committed_dataset() -> dict[str, object]:
    path = Path(__file__).resolve().parents[2] / "data" / "v1" / "dataset.json"
    return json.loads(path.read_text(encoding="utf-8"))
