from __future__ import annotations

from ahp_pipeline.models import BeaSource, FedSource, Sources
from ahp_pipeline.output import build_dataset, validate_against_schema
from ahp_pipeline.transform.capital import compute_capital
from ahp_pipeline.transform.enterprise_value import compute_enterprise_value
from ahp_pipeline.transform.flows import compute_flows, finalize_flows
from ahp_pipeline.transform.yields import compute_ratios


def test_build_dataset_round_trip(
    bea_rows, gross_investment_rows, ev_components, capital_rows
) -> None:
    panel = compute_flows(bea_rows).join(gross_investment_rows, on="period")
    panel = finalize_flows(panel)
    panel = panel.join(compute_enterprise_value(ev_components), on="period")
    panel = panel.join(compute_capital(capital_rows), on="period")
    panel = compute_ratios(panel)
    dataset = build_dataset(
        panel,
        Sources(
            bea_nipa_table_1_14=BeaSource(
                vintage="2026-03-27",
                url="https://apps.bea.gov/",
            ),
            fed_z1=FedSource(
                vintage="2026-03-13",
                release_quarter="2025Q4",
                url="https://www.federalreserve.gov/releases/z1/",
            ),
        ),
        generated_at="2026-04-13T00:00:00Z",
    )
    payload = dataset.model_dump(mode="json")
    validate_against_schema(payload)
    assert payload["periods"] == ["2024Q1", "2024Q2"]
    assert payload["stats"]["fcf_yield"]["mean"] > 0.03
