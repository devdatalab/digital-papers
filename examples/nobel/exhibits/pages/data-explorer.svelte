<!--
	Data Explorer — a bespoke, full-width page (in the left nav's "Extras" group)
	that opens the paper's underlying per-laureate analysis dataset to the reader.

	Why it exists: sections 1–6 render the paper's prose; this page is different in
	kind. It reimagines the "supplementary dataset" of a traditional publication as
	something you can look at directly in the browser. This version presents the
	dataset as a sortable, paginated table — see the design note referenced in
	CLAUDE.md: prefer changes that make the work more legible and inviting.

	The page lives at the static route `/data-explorer` (not under `[section]`,
	which is JSON-driven). The root layout gives this route its own shell mode
	(`shell--explorer`): left nav kept, right tools panel dropped, main column
	widened so the table has room. See `src/routes/+layout.svelte`.

	Upstream dependencies:
	  - $nobel/data (nobelRows, nobelMetrics, nobelMeta — curated dataset)
	  - $nobel/exhibits/NobelistsDataTable
	  - $lib/content (meta — for the document <title>)
-->
<script lang="ts">
	import { nobelRows, nobelMetrics } from '$nobel/data';
	import { meta } from '$lib/content';
	import explorerContent from '$nobel/content/data-explorer.json';
	import NobelistsDataTable from '$nobel/exhibits/NobelistsDataTable.svelte';
</script>

<svelte:head>
	<title>Raw Data Explorer — {meta.title}</title>
</svelte:head>

<article class="explorer">
	<header class="explorer-head">
		<p class="kicker ui">Explore further</p>
		<h1>Raw Data Explorer</h1>
	</header>

	<p class="intro ui">{explorerContent.introduction}</p>

	<NobelistsDataTable rows={nobelRows.slice(0, 5)} metrics={nobelMetrics} />

	<p class="footnote ui">
		Sources: <code>nobelists_analysis.csv</code> and
		<code>laureates_grounded_search.csv</code>. Percentile ranks place each laureate's father
		against the working-age male population of his country (or the world) in the nearest census
		decade. Blank cells mark values that could not be computed from the historical record.
	</p>
</article>

<style>
	.explorer {
		padding-top: 0.5rem;
	}

	.explorer-head {
		max-width: var(--read-max);
		margin-bottom: 0.85rem;
	}
	.kicker {
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--accent);
		margin: 0 0 0.6rem;
	}
	.explorer-head h1 {
		font-family: var(--font-serif);
		font-size: clamp(1.8rem, 3.5vw, 2.4rem);
		line-height: 1.15;
		font-weight: 600;
		color: var(--ink);
		margin: 0;
		letter-spacing: -0.01em;
	}
	.intro {
		max-width: var(--read-max);
		font-size: 0.85rem;
		line-height: 1.5;
		color: var(--muted);
		margin-bottom: 1.5rem;
	}

	.footnote {
		margin-top: 1rem;
		font-size: 0.78rem;
		line-height: 1.5;
		color: var(--muted);
		max-width: var(--read-max);
	}
	.footnote code {
		font-size: 0.9em;
		background: var(--bg-panel);
		padding: 0.05rem 0.3rem;
		border-radius: 3px;
	}
</style>
