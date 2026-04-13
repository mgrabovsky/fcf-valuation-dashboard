"""Manifest generation and vintage tracking."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ahp_pipeline.models import Sources


@dataclass(frozen=True)
class VintageComparison:
    has_new_vintage: bool
    details: str


def dataset_sha256(path: Path) -> str:
    """Return the SHA256 of a dataset artifact."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest(
    *,
    schema_version: str,
    generated_at: str,
    dataset_path: Path,
    sources: Sources,
) -> dict[str, Any]:
    """Build the manifest payload."""
    return {
        "schema_version": schema_version,
        "generated_at": generated_at,
        "dataset_sha256": dataset_sha256(dataset_path),
        "sources": sources.model_dump(),
    }


def compare_vintages(
    existing_manifest: dict[str, Any] | None, new_sources: Sources
) -> VintageComparison:
    """Return whether the source vintages differ from the committed manifest."""
    if existing_manifest is None:
        return VintageComparison(True, "no existing manifest")
    old_sources = existing_manifest.get("sources", {})
    new_payload = new_sources.model_dump()
    if old_sources != new_payload:
        return VintageComparison(True, "source vintages changed")
    return VintageComparison(False, "no new vintages")


def load_manifest(path: Path) -> dict[str, Any] | None:
    """Load the manifest if it exists."""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
