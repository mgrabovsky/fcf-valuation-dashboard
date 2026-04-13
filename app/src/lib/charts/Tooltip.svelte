<script lang="ts">
  export let label: string;
  export let values: Array<{ label: string; value: string; color: string }>;
</script>

<div class="pointer-events-none rounded-2xl border border-[var(--stroke)] bg-[var(--paper)] px-3 py-2 shadow-lg backdrop-blur">
  <div class="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">{label}</div>
  <div class="mt-2 space-y-1">
    {#each values as entry (entry.label)}
      <div class="flex items-center justify-between gap-4 text-sm">
        <span class="flex items-center gap-2 text-[var(--muted)]">
          <span class="h-2 w-2 rounded-full" style={`background:${entry.color}`}></span>
          {entry.label}
        </span>
        <span class="font-semibold text-[var(--ink)]">{entry.value}</span>
      </div>
    {/each}
  </div>
</div>
