<!-- Neutral cover for an agent-authored paper; depends on metadata and section manifest. -->
<script lang="ts">
  import { base } from '$app/paths';
  import { meta, manifest } from '$lib/content';
</script>
<svelte:head><title>{meta.title}</title><meta name="description" content={meta.abstract} /></svelte:head>
<article class="cover">
  <p class="ui eyebrow">Digital paper · {meta.date}</p>
  <h1>{meta.title}</h1>
  {#if meta.subtitle}<p class="subtitle">{meta.subtitle}</p>{/if}
  {#each meta.authors as author}<p class="ui">{author.name} · {author.affiliation}</p>{/each}
  <h2>Abstract</h2><p>{meta.abstract}</p>
  {#if manifest[0]}<a class="btn ui" href="{base}/{manifest[0].id}">Begin reading →</a>{/if}
  <p class="instruction ui">Ask your agent to replace this fictional paper with your manuscript. Keep the Nobel example nearby to explore richer interaction patterns.</p>
</article>
<style>
  .cover { max-width: var(--read-max); margin: 2rem auto; }
  h1 { font-size: clamp(2rem, 5vw, 3rem); line-height: 1.12; }
  .subtitle { font-size: 1.25rem; color: var(--muted); }
  .eyebrow, .instruction { color: var(--muted); font-size: 0.85rem; }
  .instruction { margin-top: 2rem; }
</style>
