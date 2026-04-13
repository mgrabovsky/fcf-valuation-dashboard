<script lang="ts">
  export let title: string;
  export let subtitle: string;
</script>

<section class="rounded-[1.75rem] border border-[var(--stroke)] bg-[var(--paper)] p-5 shadow-sm backdrop-blur">
  <div class="mb-5 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
    <div>
      <h2 class="text-xl font-semibold tracking-tight text-[var(--ink)]">{title}</h2>
      <p class="text-sm text-[var(--muted)]">{subtitle}</p>
    </div>
    <slot name="meta" />
  </div>
  <slot />
</section>
