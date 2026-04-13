<script lang="ts">
  import BrushableLineChart from '$lib/charts/BrushableLineChart.svelte';
  import TwinAxisChart from '$lib/charts/TwinAxisChart.svelte';
  import ChartCard from '$lib/components/ChartCard.svelte';
  import DataFootnote from '$lib/components/DataFootnote.svelte';
  import StatCard from '$lib/components/StatCard.svelte';
  import { dataset } from '$lib/data/dataset';
  import { formatPercent, formatRatio } from '$lib/data/format';
  import { buildComplementSeries, buildSeries, datasetSummary } from '$lib/data/selectors';

  const summary = datasetSummary(dataset);
  const periods = dataset.periods;

  const fcfYieldSeries = [
    buildSeries(periods, 'fcf-yield', 'FCF yield', 'var(--accent)', dataset.series.fcf_yield)
  ];
  const valuationSeries = [
    buildSeries(periods, 'ev-gva', 'EV / GVA', 'var(--accent)', dataset.series.ev_gva),
    buildSeries(periods, 'k-gva', 'K / GVA', 'var(--accent-3)', dataset.series.k_gva)
  ];
  const netInvKSeries = [
    buildSeries(periods, 'net-inv-k', 'Net investment / K', 'var(--accent)', dataset.series.net_inv_k)
  ];
  const kVSeries = [
    buildSeries(periods, 'k-v', 'K / V', 'var(--accent-2)', dataset.series.k_v)
  ];
</script>

<svelte:head>
  <title>Macro FCF Valuation Dashboard</title>
  <meta name="description" content="Static dashboard for AHP macro valuation series." />
</svelte:head>

<div class="mx-auto max-w-7xl px-4 py-8 md:px-6 md:py-10">
  <header class="rounded-[2rem] border border-[var(--stroke)] bg-[var(--paper)] p-6 shadow-sm backdrop-blur md:p-8">
    <p class="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--muted)]">AHP Macro Valuation Dashboard</p>
    <h1 class="mt-4 max-w-3xl text-4xl font-semibold tracking-tight text-[var(--ink)] md:text-6xl">
      Static reproduction of the macroeconomic free-cash-flow yield.
    </h1>
    <p class="mt-4 max-w-2xl text-base leading-7 text-[var(--muted)] md:text-lg">
      Build-time JSON import, no runtime fetches, and quarterly accounting identities enforced in the pipeline.
    </p>
    <div class="mt-6 flex flex-wrap gap-3 text-sm text-[var(--muted)]">
      <span>Generated {dataset.generated_at}</span>
      <span>Fed Z.1 {dataset.sources.fed_z1.vintage}</span>
      <span>BEA {dataset.sources.bea_nipa_table_1_14.vintage}</span>
    </div>
  </header>

  <section class="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
    <StatCard
      label="Latest FCF Yield"
      value={formatPercent(summary.latestFcfYield, 2)}
      detail={`Historical mean ${formatPercent(summary.meanFcfYield, 2)}`}
    />
    <StatCard
      label="Deviation"
      value={`${summary.deviationPp >= 0 ? '+' : ''}${summary.deviationPp.toFixed(2)}pp`}
      detail="Latest minus full-sample mean"
    />
    <StatCard
      label="Latest Earnings Yield"
      value={formatPercent(summary.latestEarningsYield, 2)}
      detail="Trailing sample endpoint"
    />
    <StatCard label="Latest EV / GVA" value={formatRatio(summary.latestEvGva, 2)} detail="Enterprise value to gross value added" />
  </section>

  <section class="mt-6 space-y-6">
    <ChartCard title="Free Cash Flow Yield" subtitle="Primary series with full-sample mean and minus-one-sigma reference lines.">
      <BrushableLineChart
        testId="chart-fcf-yield"
        {periods}
        series={fcfYieldSeries}
        formatter={(value) => formatPercent(value, 2)}
        referenceLines={[
          { label: 'Mean', value: dataset.stats.fcf_yield.mean, color: 'rgba(17, 100, 102, 0.4)' },
          {
            label: 'Mean - 1σ',
            value: dataset.stats.fcf_yield.mean - dataset.stats.fcf_yield.std,
            color: 'rgba(208, 102, 63, 0.4)'
          }
        ]}
      />
    </ChartCard>

    <ChartCard title="Valuation vs Capital Intensity" subtitle="Figure 1 style comparison of EV / GVA and K / GVA.">
      <BrushableLineChart
        testId="chart-valuation"
        {periods}
        series={valuationSeries}
        formatter={(value) => formatRatio(value, 2)}
      />
    </ChartCard>

    <ChartCard title="Cash Flow and Labor Wedge" subtitle="Figure 2 style twin-axis comparison of FCF / GVA and 1 - labor share.">
      <TwinAxisChart
        testId="chart-twin-axis"
        {periods}
        leftSeries={buildSeries(periods, 'fcf-gva', 'FCF / GVA', 'var(--accent-2)', dataset.series.fcf_gva)}
        rightSeries={buildComplementSeries(periods, 'one-minus-labor', '1 - labor share', 'var(--accent-3)', dataset.series.labor_share)}
        leftFormatter={(value) => formatPercent(value, 1)}
        rightFormatter={(value) => formatPercent(value, 1)}
      />
    </ChartCard>

    <div class="grid gap-6 xl:grid-cols-2">
      <ChartCard title="Net Investment / K" subtitle="Figure 5a style panel.">
        <BrushableLineChart
          testId="chart-net-inv-k"
          {periods}
          series={netInvKSeries}
          formatter={(value) => formatPercent(value, 2)}
        />
      </ChartCard>
      <ChartCard title="K / V" subtitle="Figure 5b style panel.">
        <BrushableLineChart
          testId="chart-k-v"
          {periods}
          series={kVSeries}
          formatter={(value) => formatRatio(value, 2)}
        />
      </ChartCard>
    </div>
  </section>

  <div class="mt-6">
    <DataFootnote
      generatedAt={dataset.generated_at}
      fedVintage={dataset.sources.fed_z1.vintage}
      beaVintage={dataset.sources.bea_nipa_table_1_14.vintage}
    />
  </div>
</div>

