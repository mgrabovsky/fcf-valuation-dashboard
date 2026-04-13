from __future__ import annotations

from ahp_pipeline.models import Dataset
from ahp_pipeline.validate import validate_dataset


def test_validate_committed_dataset(committed_dataset) -> None:
    dataset = Dataset.model_validate(committed_dataset)
    validate_dataset(dataset)
