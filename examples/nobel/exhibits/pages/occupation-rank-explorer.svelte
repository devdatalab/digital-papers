<!--
	Occupation Explorer — a bespoke, full-width Extras page stacking three
	views of laureate father occupations:
	  1. OccupationRankChart — how a selected occupation's U.S. income and
	     education percentile ranks moved across census decades 1850–1970.
	  2. OccupationTable — the complete searchable/sortable representation table
	     at the 10-group, 25-group, and detailed occupation levels.
	  3. AppendixTable — the detailed occupation-to-group classification crosswalk
	     previously shown in the occupation-classification supplementary popup.

	The chart and tables live on one page (chart above, table below an in-page anchor) so a reader
	can move from the trajectory of a single occupation to the full cross-section
	without a route change. The chart and table answer intentionally different
	questions: the chart is U.S.-only per-decade; the table's averages weight
	country–decade cells to the laureate sample and are not U.S.-only.

	The route sits in the left nav's "Extras" group and gets the wide explorer
	shell (`shell--explorer`) from the root layout (see `explorerRoutes` in
	src/routes/+layout.svelte).

	Upstream dependencies:
	  - $lib/content (meta — for the document <title>)
	  - $nobel/exhibits/OccupationRankChart, $nobel/exhibits/OccupationTable,
	    $nobel/exhibits/AppendixTable
-->
<script lang="ts">
	import { meta } from '$lib/content';
	import OccupationRankChart from '$nobel/exhibits/OccupationRankChart.svelte';
	import OccupationTable from '$nobel/exhibits/OccupationTable.svelte';
	import AppendixTable from '$nobel/exhibits/AppendixTable.svelte';
</script>

<svelte:head>
	<title>Occupation Explorer — {meta.title}</title>
</svelte:head>

<article class="explorer">
	<header class="explorer-head">
		<p class="kicker ui">Explore further</p>
		<h1>Occupation Explorer</h1>
		<p class="lede ui">These were intermediate exhibits that we created to better understand our occupational data. It's great to share these with readers so that they can understand how your measures were created as well.</p>
	</header>

	<section class="chart-section" aria-label="Rank over time">
		<OccupationRankChart />
	</section>

	<section class="table-section" aria-label="Occupation table">
		<h2 id="occupation-table">Complete occupation table</h2>
		<p class="note ui">
			“Expected fathers” is how many laureate fathers an occupation would supply if laureates were
			drawn in proportion to the population; “over-representation” is the ratio of the actual to the
			expected share. Table averages weight country–decade occupation cells to match where and when
			laureates were born. They therefore summarize the international laureate sample and need not
			equal the U.S.-only trajectories in the Occupation Explorer above.
		</p>
		<OccupationTable />
	</section>
	<section class="table-section" aria-labelledby="occupation-classification">
		<h2 id="occupation-classification">Occupation classification</h2>
		<p class="note ui">
			How each detailed occupation is assigned to the 10- and 25-group aggregations used in the
			occupation-share tables.
		</p>
		<AppendixTable table="occ_freq" hideHeading />
	</section>
</article>

<style>
	.explorer {
		padding-top: 0.5rem;
	}
	.explorer-head {
		max-width: var(--read-max);
		margin-bottom: 2rem;
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
		margin: 0 0 1rem;
		letter-spacing: -0.01em;
	}
	.lede {
		font-size: 0.85rem;
		line-height: 1.5;
		color: var(--muted);
		margin: 0;
	}
	.chart-section {
		margin-bottom: 3rem;
	}
	.table-section + .table-section {
		margin-top: 3rem;
	}

	.table-section h2 {
		font-family: var(--font-serif);
		font-size: 1.4rem;
		font-weight: 600;
		color: var(--ink);
		margin: 0 0 0.6rem;
		scroll-margin-top: 1rem;
	}
	.note {
		max-width: var(--read-max);
		font-size: 0.85rem;
		line-height: 1.55;
		color: var(--muted);
		margin: 0 0 1.25rem;
	}
</style>
