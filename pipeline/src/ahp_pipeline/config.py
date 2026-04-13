"""Configuration helpers for the AHP ETL pipeline."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
PIPELINE_DIR = ROOT_DIR / "pipeline"
CACHE_DIR = PIPELINE_DIR / ".cache"
DATA_DIR = ROOT_DIR / "data" / "v1"
SCHEMA_PATH = ROOT_DIR / "schema" / "v1" / "dataset.schema.json"
DATASET_PATH = DATA_DIR / "dataset.json"
MANIFEST_PATH = DATA_DIR / "manifest.json"

BEA_API_URL = "https://apps.bea.gov/api/data"
BEA_TABLE_NAME = "T11400"
FED_Z1_ZIP_URL = "https://www.federalreserve.gov/releases/z1/current/z1_csv_files.zip"


def require_bea_api_key() -> str:
    """Return the BEA API key or fail loudly."""
    value = os.getenv("BEA_API_KEY")
    if not value:
        message = "BEA_API_KEY is required to run the pipeline."
        raise RuntimeError(message)
    return value


def ensure_cache_dir() -> Path:
    """Create and return the cache directory."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def cache_path(prefix: str, key: str, suffix: str) -> Path:
    """Create a stable cache path from a logical key."""
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return ensure_cache_dir() / f"{prefix}-{digest}.{suffix}"
