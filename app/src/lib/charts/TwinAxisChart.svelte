<script lang="ts">
  import Tooltip from '$lib/charts/Tooltip.svelte';
  import { chartDimensions, linePath, nearestIndex, visiblePoints, xScale, yScale } from '$lib/charts/chart-utils';
  import type { ChartSeries } from '$lib/data/selectors';

  export let testId: string;
  export let periods: string[];
  export let leftSeries: ChartSeries;
  export let rightSeries: ChartSeries;
  export let leftFormatter: (value: number) => string;
  export let rightFormatter: (value: number) => string;

  let hoveredIndex: number | null = null;

  $: leftPoints = visiblePoints(leftSeries);
  $: rightPoints = visiblePoints(rightSeries);
  $: x = xScale(leftPoints.length || 1);
  $: leftY = yScale([
    Math.min(...leftPoints.map((point) => point.value)) * 0.94,
    Math.max(...leftPoints.map((point) => point.value)) * 1.06
  ]);
  $: rightY = yScale([
    Math.min(...rightPoints.map((point) => point.value)) * 0.94,
    Math.max(...rightPoints.map((point) => point.value)) * 1.06
  ]);

  function onMove(event: MouseEvent) {
    const svg = event.currentTarget as SVGSVGElement;
    const rect = svg.getBoundingClientRect();
    hoveredIndex = nearestIndex(
      ((event.clientX - rect.left) / rect.width) * chartDimensions.width,
      periods.length
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
    <path d={linePath(leftPoints, x, leftY)} fill="none" stroke={leftSeries.color} stroke-width="3" />
    <path d={linePath(rightPoints, x, rightY)} fill="none" stroke={rightSeries.color} stroke-width="3" />
  </svg>

  {#if hoveredIndex !== null}
    <div class="absolute right-3 top-3">
      <Tooltip
        label={periods[hoveredIndex] ?? ''}
        values={[
          {
            label: leftSeries.label,
            value: leftFormatter(leftPoints[hoveredIndex]?.value ?? 0),
            color: leftSeries.color
          },
          {
            label: rightSeries.label,
            value: rightFormatter(rightPoints[hoveredIndex]?.value ?? 0),
            color: rightSeries.color
          }
        ]}
      />
    </div>
  {/if}
</div>

