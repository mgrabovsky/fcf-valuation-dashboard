<script lang="ts">
  import Tooltip from '$lib/charts/Tooltip.svelte';
  import type { ReferenceLine } from '$lib/charts/types';
  import {
    chartDimensions,
    linePath,
    nearestIndex,
    valueExtent,
    visiblePoints,
    xScale,
    yScale
  } from '$lib/charts/chart-utils';
  import type { ChartSeries } from '$lib/data/selectors';

  export let testId: string;
  export let periods: string[];
  export let series: ChartSeries[];
  export let formatter: (value: number) => string;
  export let referenceLines: ReferenceLine[] = [];
  export let domainStart = 0;
  export let domainEnd = 0;

  let hoveredIndex: number | null = null;

  $: domain = { start: domainStart, end: domainEnd };
  $: visibleSeries = series.map((item) => ({ ...item, points: visiblePoints(item, domain) }));
  $: visiblePeriods = periods.slice(domain.start, domain.end + 1);
  $: x = xScale(Math.max(visibleSeries[0]?.points.length ?? 1, 1));
  $: extent = valueExtent(series, domain);
  $: y = yScale(extent);
  $: activeIndex = hoveredIndex ?? 0;
  $: tooltipValues =
    hoveredIndex === null
      ? []
      : visibleSeries.map((item) => ({
          label: item.label,
          value: formatter(item.points[activeIndex]?.value ?? 0),
          color: item.color
        }));

  function onMove(event: MouseEvent) {
    const svg = event.currentTarget as SVGSVGElement;
    const rect = svg.getBoundingClientRect();
    hoveredIndex = nearestIndex(
      ((event.clientX - rect.left) / rect.width) * chartDimensions.width,
      visiblePeriods.length
    );
  }
</script>

<div class="relative" data-testid={testId}>
  <svg
    class="h-auto w-full overflow-visible"
    role="img"
    aria-label={testId}
    viewBox={`0 0 ${chartDimensions.width} ${chartDimensions.height}`}
    onmouseleave={() => (hoveredIndex = null)}
    onmousemove={onMove}
  >
    {#each referenceLines as reference (reference.label)}
      <line
        x1={chartDimensions.marginLeft}
        y1={y(reference.value)}
        x2={chartDimensions.width - chartDimensions.marginRight}
        y2={y(reference.value)}
        stroke={reference.color}
        stroke-dasharray={reference.dashArray ?? '6 4'}
        stroke-width="1.5"
      />
    {/each}

    {#each visibleSeries as item (item.id)}
      <path d={linePath(item.points, x, y)} fill="none" stroke={item.color} stroke-width="3" />
    {/each}

    {#if hoveredIndex !== null}
      <line
        x1={x(hoveredIndex)}
        y1={chartDimensions.marginTop}
        x2={x(hoveredIndex)}
        y2={chartDimensions.height - chartDimensions.marginBottom}
        stroke="rgba(23, 33, 31, 0.18)"
        stroke-width="1"
      />
    {/if}

    <rect
      x={chartDimensions.marginLeft}
      y={chartDimensions.marginTop}
      width={chartDimensions.width - chartDimensions.marginLeft - chartDimensions.marginRight}
      height={chartDimensions.height - chartDimensions.marginTop - chartDimensions.marginBottom}
      fill="transparent"
    />
  </svg>

  {#if hoveredIndex !== null}
    <div class="absolute right-3 top-3">
      <Tooltip label={visiblePeriods[hoveredIndex] ?? ''} values={tooltipValues} />
    </div>
  {/if}
</div>
