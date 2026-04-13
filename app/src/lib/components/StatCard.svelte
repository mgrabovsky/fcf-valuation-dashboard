<script lang="ts">
  export let label: string;
  export let value: string;
  export let detail: string;
</script>

<article class="rounded-[1.5rem] border border-[var(--stroke)] bg-[var(--paper)] p-5 shadow-sm backdrop-blur">
  <p class="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">{label}</p>
  <p class="mt-3 text-3xl font-semibold text-[var(--ink)]">{value}</p>
  <p class="mt-2 text-sm text-[var(--muted)]">{detail}</p>
</article>
