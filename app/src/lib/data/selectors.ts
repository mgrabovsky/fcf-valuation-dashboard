import { parsePeriod } from "$lib/data/format";
import type { Dataset, DatasetSeriesEntry } from "$lib/types/dataset";

export interface ChartPoint {
  period: string;
  date: Date;
  value: number;
}

export interface ChartSeries {
  id: string;
  label: string;
  color: string;
  points: ChartPoint[];
}

export function seriesPoints(
  periods: string[],
  series: DatasetSeriesEntry,
): ChartPoint[] {
  return periods.flatMap((period, index) => {
    const value = series.values[index];
    if (value === null) {
      return [];
    }
    return [{ period, date: parsePeriod(period), value }];
  });
}

export function buildSeries(
  periods: string[],
  id: string,
  label: string,
  color: string,
  series: DatasetSeriesEntry,
): ChartSeries {
  return { id, label, color, points: seriesPoints(periods, series) };
}

export function buildComplementSeries(
  periods: string[],
  id: string,
  label: string,
  color: string,
  series: DatasetSeriesEntry,
): ChartSeries {
  return {
    id,
    label,
    color,
    points: periods.flatMap((period, index) => {
      const value = series.values[index];
      if (value === null) {
        return [];
      }
      return [{ period, date: parsePeriod(period), value: 1 - value }];
    }),
  };
}

export function latestValue(series: DatasetSeriesEntry): number | null {
  for (let index = series.values.length - 1; index >= 0; index -= 1) {
    const value = series.values[index];
    if (value !== null) {
      return value;
    }
  }
  return null;
}

export function datasetSummary(dataset: Dataset) {
  const latestFcfYield = latestValue(dataset.series.fcf_yield) ?? 0;
  const meanFcfYield = dataset.stats.fcf_yield.mean;
  return {
    latestFcfYield,
    meanFcfYield,
    deviationPp: (latestFcfYield - meanFcfYield) * 100,
    latestEarningsYield: latestValue(dataset.series.earnings_yield) ?? 0,
    latestEvGva: latestValue(dataset.series.ev_gva) ?? 0,
  };
}
