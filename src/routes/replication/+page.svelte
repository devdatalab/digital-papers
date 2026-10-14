<!-- Reproduction and remix instructions shared by all papers; depends on the selected download inventory. -->
<script lang="ts">
  import { base } from '$app/paths';
  import { meta } from '$lib/content';
  import paperConfig from '$paper/paper.config';
  import { codeAnchorId } from '$lib/reading/replicationSource';
  import type { PageData } from './$types';
  let { data }: { data: PageData } = $props();
  const codeFiles = $derived(data.files.filter((file) => file.endsWith('.py')));
  const anchors = $derived([...new Set(codeFiles.map(file => codeAnchorId(file.replace(/^package\/code\//, '').replace(/^generators\//, ''))))]);
</script>
<svelte:head><title>Replicate or remix — {meta.title}</title></svelte:head>
<article>
  <p class="ui kicker">Explore further</p><h1>Replicate or remix</h1>
  {#if paperConfig.replicationIntro}<p class="lede ui">{paperConfig.replicationIntro}</p>{/if}
  <p>Every scientific exhibit displayed in this example is covered by the reproduction bundle. It contains the generating code, required inputs, and instructions. Declared manual transcriptions and external metadata are documented separately.</p>
  <p><a class="btn ui" href="{base}/downloads/reproduction.zip">Download reproduction bundle ↓</a></p>
  <h2>Rebuild the exhibits</h2>
  <p>Extract the bundle, read its README, then run <code>python make_all.py --check</code> from the reproduction folder. The check compares regenerated data with the shipped results. Follow the README to install any required Python dependencies.</p>
  <h2>Adapt with a local agent</h2>
  <p>Give your agent the manuscript and the code used to make its figures. Ask it to preserve the paper text, captions and notes exactly; reuse the analysis code or rebuild it in Python; and provide reproduction code for every displayed exhibit.</p>
  <details><summary>Suggested prompt</summary><blockquote>Read AGENTS.md and docs/adapt-a-paper.md. My manuscript, bibliography and analysis code are at [local project path]. Copy examples/nobel into papers/&lt;paper-name&gt; and adapt it for my paper. Preserve scientific content exactly unless I request a change. Reproduce every displayed exhibit and report any source discrepancies. Use the Nobel example for presentation ideas.</blockquote></details>
  <h2>Code and inputs</h2>
  {#each anchors as anchor}<details id={anchor}><summary>{anchor.replace('code-', '')}</summary><ul>{#each codeFiles.filter(file => codeAnchorId(file.replace(/^package\/code\//, '').replace(/^generators\//, '')) === anchor) as file}<li><a href="{base}/downloads/reproduction/{file}">{file}</a></li>{/each}</ul></details>{/each}
  <details><summary>Browse all {data.files.length} reproduction files</summary><ul>{#each data.files as file}<li><a href="{base}/downloads/reproduction/{file}">{file}</a></li>{/each}</ul></details>
</article>
<style>article { max-width: var(--read-max); } .lede { font-size: 0.85rem; line-height: 1.5; color: var(--muted); margin: 0 0 1.5rem; } .kicker { color: var(--muted); font-size: 0.8rem; } li { font-size: 0.85rem; } blockquote { color: var(--muted); }</style>
