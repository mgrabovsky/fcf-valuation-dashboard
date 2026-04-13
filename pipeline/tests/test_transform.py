from __future__ import annotations

from ahp_pipeline.transform.capital import compute_capital
from ahp_pipeline.transform.enterprise_value import compute_enterprise_value
from ahp_pipeline.transform.flows import compute_flows
from ahp_pipeline.transform.yields import compute_ratios


def test_compute_flows(bea_rows) -> None:
    frame = compute_flows(bea_rows)
    first = frame.row(0, named=True)
    assert first["net_investment"] == 3.8
    assert first["fcf"] == 22.0
    assert first["earnings"] == 25.8


def test_compute_enterprise_value(ev_components) -> None:
    frame = compute_enterprise_value(ev_components)
    assert frame.get_column("enterprise_value").to_list() == [700.0, 705.0]


def test_compute_capital(capital_rows) -> None:
    frame = compute_capital(capital_rows)
    assert frame.columns == ["period", "capital_replacement_cost"]


def test_compute_ratios(bea_rows, ev_components, capital_rows) -> None:
    panel = compute_flows(bea_rows)
    panel = panel.join(compute_enterprise_value(ev_components), on="period")
    panel = panel.join(compute_capital(capital_rows), on="period")
    ratios = compute_ratios(panel)
    first = ratios.row(0, named=True)
    assert round(first["fcf_yield"], 6) == 0.031429
    assert round(first["k_v"], 6) == 0.431429
