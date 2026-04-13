import { scaleLinear } from "d3-scale";
import { line } from "d3-shape";
import type { ChartPoint, ChartSeries } from "$lib/data/selectors";

export interface Dimensions {
  width: number;
  height: number;
  marginTop: number;
  marginRight: number;
  marginBottom: number;
  marginLeft: number;
}

export const chartDimensions: Dimensions = {
  width: 920,
  height: 340,
  marginTop: 20,
  marginRight: 20,
  marginBottom: 38,
  marginLeft: 56,
};

export interface VisibleDomain {
  start: number;
  end: number;
}

export function visiblePoints(
  series: ChartSeries,
  domain?: VisibleDomain,
): ChartPoint[] {
  if (!domain) {
    return series.points;
  }
  return series.points.slice(domain.start, domain.end + 1);
}

export function valueExtent(
  series: ChartSeries[],
  domain?: VisibleDomain,
): [number, number] {
  const values = series.flatMap((item) =>
    visiblePoints(item, domain).map((point) => point.value),
  );
  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding = (max - min || 1) * 0.12;
  return [min - padding, max + padding];
}

export function xScale(
  length: number,
  dimensions: Dimensions = chartDimensions,
) {
  return scaleLinear()
    .domain([0, Math.max(length - 1, 1)])
    .range([dimensions.marginLeft, dimensions.width - dimensions.marginRight]);
}

export function yScale(
  extent: [number, number],
  dimensions: Dimensions = chartDimensions,
) {
  return scaleLinear()
    .domain(extent)
    .range([dimensions.height - dimensions.marginBottom, dimensions.marginTop]);
}

export function linePath(
  points: ChartPoint[],
  x = xScale(points.length || 1),
  y = yScale([0, 1]),
): string {
  const generator = line<ChartPoint>()
    .x((point, index) => x(index))
    .y((point) => y(point.value));
  return generator(points) ?? "";
}

export function nearestIndex(
  xPosition: number,
  length: number,
  dimensions: Dimensions = chartDimensions,
): number {
  const start = dimensions.marginLeft;
  const end = dimensions.width - dimensions.marginRight;
  const clamped = Math.min(Math.max(xPosition, start), end);
  const ratio = (clamped - start) / (end - start || 1);
  return Math.round(ratio * Math.max(length - 1, 0));
}
