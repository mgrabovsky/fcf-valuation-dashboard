"""Pydantic models matching the dataset contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BeaSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vintage: str
    url: str


class FedSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vintage: str
    release_quarter: str
    url: str


class Sources(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bea_nipa_table_1_14: BeaSource
    fed_z1: FedSource


class Series(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    description: str
    unit: Literal["level", "ratio"]
    values: list[float | None] = Field(min_length=1)


class Stats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mean: float
    std: float
    min: float
    max: float


class DatasetSeries(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gva: Series
    labor_compensation: Series
    taxes_total: Series
    gross_investment: Series
    cfc: Series
    net_investment: Series
    fcf: Series
    earnings: Series
    enterprise_value: Series
    capital_replacement_cost: Series
    fcf_yield: Series
    earnings_yield: Series
    ev_gva: Series
    k_gva: Series
    fcf_gva: Series
    labor_share: Series
    net_inv_v: Series
    net_inv_k: Series
    k_v: Series
    payout_ratio: Series


class DatasetStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fcf_yield: Stats
    earnings_yield: Stats
    ev_gva: Stats
    k_gva: Stats
    fcf_gva: Stats
    labor_share: Stats
    net_inv_v: Stats
    net_inv_k: Stats
    k_v: Stats
    payout_ratio: Stats


class Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"]
    generated_at: str
    sources: Sources
    frequency: Literal["quarterly"]
    periods: list[str] = Field(min_length=1)
    series: DatasetSeries
    stats: DatasetStats
