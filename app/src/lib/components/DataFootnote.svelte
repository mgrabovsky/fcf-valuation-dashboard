<script lang="ts">
  export let generatedAt: string;
  export let fedVintage: string;
  export let beaVintage: string;
</script>

<footer class="rounded-[1.75rem] border border-[var(--stroke)] bg-[var(--paper)] p-5 text-sm text-[var(--muted)] shadow-sm backdrop-blur">
  <p>Generated: {generatedAt}. Fed Z.1 vintage: {fedVintage}. BEA vintage: {beaVintage}.</p>
  <p class="mt-2">
    Sources: BEA NIPA Table 1.14, Federal Reserve Z.1, and Atkeson, Heathcote, and Perri (2026).
  </p>
</footer>
