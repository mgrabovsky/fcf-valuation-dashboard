  <script lang="ts">
  import LineChart from '$lib/charts/LineChart.svelte';
  import type { ReferenceLine } from '$lib/charts/types';
  import { chartDimensions, linePath, xScale, yScale } from '$lib/charts/chart-utils';
  import type { ChartSeries } from '$lib/data/selectors';

  export let testId: string;
  export let periods: string[];
  export let series: ChartSeries[];
  export let formatter: (value: number) => string;
  export let referenceLines: ReferenceLine[] = [];

  let start = 0;
  let end = 0;

  $: if (periods.length > 0 && end === 0) {
    end = periods.length - 1;
  }
  $: safeStart = Math.min(start, end);
  $: safeEnd = Math.max(start, end);
  $: overviewPoints = series[0]?.points ?? [];
  $: overviewX = xScale(overviewPoints.length || 1);
  $: overviewY = yScale([
    Math.min(...overviewPoints.map((point) => point.value)) * 0.95,
    Math.max(...overviewPoints.map((point) => point.value)) * 1.05
  ]);
</script>

<div class="space-y-4" data-testid={testId}>
  <LineChart
    testId={`${testId}-main`}
    {periods}
    {series}
    {formatter}
    {referenceLines}
    domainStart={safeStart}
    domainEnd={safeEnd}
  />

  <div class="rounded-2xl border border-[var(--stroke)] bg-white/60 p-3">
    <svg class="h-20 w-full" viewBox={`0 0 ${chartDimensions.width} 96`}>
      <path
        d={linePath(overviewPoints, overviewX, overviewY)}
        fill="none"
        stroke={series[0]?.color ?? '#116466'}
        stroke-width="2"
      />
      <rect
        x={overviewX(safeStart)}
        y="8"
        width={Math.max(overviewX(safeEnd) - overviewX(safeStart), 10)}
        height="72"
        fill="rgba(17, 100, 102, 0.12)"
        stroke="rgba(17, 100, 102, 0.35)"
        stroke-width="2"
      />
    </svg>
    <div class="mt-3 grid gap-3 md:grid-cols-2">
      <label class="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
        Start
        <input
          class="mt-2 w-full accent-[var(--accent)]"
          type="range"
          min="0"
          max={periods.length - 1}
          bind:value={start}
        />
      </label>
      <label class="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
        End
        <input
          class="mt-2 w-full accent-[var(--accent)]"
          type="range"
          min="0"
          max={periods.length - 1}
          bind:value={end}
        />
      </label>
    </div>
  </div>
</div>
