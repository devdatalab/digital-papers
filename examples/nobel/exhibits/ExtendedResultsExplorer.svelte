<!--
	ExtendedResultsExplorer — the body of the /extended-results Extras page.

	Why this file exists:
		Reimagines the standalone nobel-agents/main_results dashboard as a native
		part of this edition. Two selectors — SES measure and subgroup — drive a
		2×2 grid of four charts (father-rank histogram + average-rank, top-10%, and
		top-20% prize-year binscatters) for the chosen slice. This surfaces the
		full SES-measure × outcome × subgroup permutation grid (99 trend panels)
		that the printed paper never enumerates, in one compact interactive view.

		Region subgroups are uninformative for global income ranks (region is the
		main factor driving global-rank differences), so the "By region" group is
		disabled under the global-income measure and, if a region was selected, the
		choice falls back to Overall — mirroring the reference dashboard's rule.

		All numbers are precomputed at build time by the extended_results extractor
		(same HC1 robust SEs, 5-year windows, and pooled interacted subgroup slopes
		as the reference). Charts compose ddl-charts primitives via the two child
		components rather than re-hand-rolling D3.

	Upstream dependencies:
		$nobel/data (extendedResultsData + Extended* types)
		./ExtendedHistogram.svelte, ./ExtendedTrendChart.svelte
-->
<script lang="ts">
	import {
		extendedResultsData,
		type ExtendedPanelId,
		type ExtendedSubgroup
	} from '$nobel/data';
	import ExtendedHistogram from './ExtendedHistogram.svelte';
	import ExtendedTrendChart from './ExtendedTrendChart.svelte';

	const { measures, subgroups, cells } = extendedResultsData;

	// Subgroups grouped by dimension for the native <optgroup> selector.
	const bySubDim = (dim: ExtendedSubgroup['dim']) => subgroups.filter((s) => s.dim === dim);
	const fieldSubs = bySubDim('field');
	const genderSubs = bySubDim('gender');
	const regionSubs = bySubDim('region');
	const subgroupLabel = (id: string) => subgroups.find((s) => s.id === id)?.label ?? id;

	const TREND_PANELS: { id: ExtendedPanelId; title: string; yLabel: string; asPercent: boolean }[] = [
		{ id: 'average_rank', title: 'Average rank', yLabel: 'Average rank', asPercent: false },
		{ id: 'top_10', title: 'Share in top 10%', yLabel: '% in top 10%', asPercent: true },
		{ id: 'top_20', title: 'Share in top 20%', yLabel: '% in top 20%', asPercent: true }
	];

	const GLOBAL_ID = 'global_income';

	let measureId = $state(measures[0].id);
	let subgroupId = $state('overall');

	let regionSuppressed = $derived(measureId === GLOBAL_ID);

	// If region is disabled by switching to global income, drop back to Overall.
	$effect(() => {
		if (regionSuppressed && subgroups.find((s) => s.id === subgroupId)?.dim === 'region') {
			subgroupId = 'overall';
		}
	});

	let activeMeasure = $derived(measures.find((m) => m.id === measureId) ?? measures[0]);
	// Guard against a missing cell (e.g. a region id under global income) by
	// falling back to the overall cell for the active measure.
	let cell = $derived(cells[measureId]?.[subgroupId] ?? cells[measureId].overall);

	// "1901: 92.7 → 2023: 83.7" endpoint summary under each trend chart.
	function endpointSummary(panelId: ExtendedPanelId, asPercent: boolean): string | null {
		const fit = cell.panels[panelId].fit;
		if (fit.predStart.y == null || fit.predEnd.y == null) return null;
		const fmt = (v: number) => (asPercent ? `${v.toFixed(0)}%` : v.toFixed(0));
		return `${fit.predStart.x}: ${fmt(fit.predStart.y)} → ${fit.predEnd.x}: ${fmt(fit.predEnd.y)}`;
	}
</script>

<div class="controls ui">
	<div class="control-group">
		<span class="control-label">SES measure</span>
		<div class="segmented" role="tablist" aria-label="SES measure">
			{#each measures as m (m.id)}
				<button
					role="tab"
					aria-selected={measureId === m.id}
					class:active={measureId === m.id}
					onclick={() => (measureId = m.id)}
				>{m.short}</button>
			{/each}
		</div>
	</div>

	<div class="control-group">
		<label class="control-label" for="subgroup-select">Subgroup</label>
		<select id="subgroup-select" bind:value={subgroupId}>
			<option value="overall">Overall</option>
			<optgroup label="By field">
				{#each fieldSubs as s (s.id)}
					<option value={s.id}>{s.label}</option>
				{/each}
			</optgroup>
			<optgroup label="By gender">
				{#each genderSubs as s (s.id)}
					<option value={s.id}>{s.label}</option>
				{/each}
			</optgroup>
			<optgroup label="By region" disabled={regionSuppressed}>
				{#each regionSubs as s (s.id)}
					<option value={s.id}>{s.label}</option>
				{/each}
			</optgroup>
		</select>
	</div>
</div>

<p class="active-context ui">
	<strong>{activeMeasure.label}</strong> · {subgroupLabel(subgroupId)} ·
	{cell.n.toLocaleString()} laureates
</p>

{#if regionSuppressed}
	<p class="region-note ui" role="note">
		Region breakdowns aren't shown for global income ranks — region is the main factor driving
		global-rank differences.
	</p>
{/if}

<div class="chart-grid">
	<figure class="chart-card">
		<figcaption class="chart-title">Distribution of father ranks</figcaption>
		<ExtendedHistogram bars={cell.histogram} />
		<p class="chart-sub ui">Share of laureates in each 5-percentile bin.</p>
	</figure>

	{#each TREND_PANELS as panel (panel.id)}
		<figure class="chart-card">
			<figcaption class="chart-title">{panel.title}</figcaption>
			<ExtendedTrendChart
				points={cell.panels[panel.id].points}
				fit={cell.panels[panel.id].fit}
				yLabel={panel.yLabel}
				asPercent={panel.asPercent}
			/>
			{#if endpointSummary(panel.id, panel.asPercent)}
				<p class="chart-sub ui">{endpointSummary(panel.id, panel.asPercent)}</p>
			{/if}
		</figure>
	{/each}
</div>

<p class="footnote ui">
	Each trend point is a mean over a 5-year prize-year window, plotted at the window midpoint (hover
	for values). The dashed red line is an OLS fit; <code>b</code> is the slope per year with
	robust standard errors (<code>*** p&lt;.01, ** p&lt;.05, * p&lt;.1</code>). Overall fits use a
	per-sample regression; field, gender, and region slopes come from a single pooled interacted model
	(the paper's Table A12 structure). Top-10%/top-20% panels recode each father's rank to 0 or 100
	(≥90th, ≥80th percentile) before averaging. Source: computed from
	<code>data/nobelists_analysis.csv</code> in the replication package.
</p>

<style>
	.controls {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem 2rem;
		align-items: flex-end;
		padding: 1rem 1.1rem;
		border: 1px solid var(--rule);
		border-radius: 8px;
		background: var(--bg-panel);
		margin-bottom: 1rem;
	}
	.control-group {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
	.control-label {
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--muted);
	}
	.segmented {
		display: flex;
		gap: 0.25rem;
		flex-wrap: wrap;
	}
	.segmented button {
		font-family: var(--font-ui);
		font-size: 0.82rem;
		padding: 0.35rem 0.7rem;
		border: 1px solid var(--rule-strong);
		border-radius: 3px;
		background: var(--bg);
		color: var(--ink-soft);
		cursor: pointer;
		transition: background 0.1s, color 0.1s;
	}
	.segmented button.active {
		background: var(--accent);
		color: #fff;
		border-color: var(--accent);
	}
	#subgroup-select {
		font-family: var(--font-ui);
		font-size: 0.9rem;
		padding: 0.4rem 0.6rem;
		border: 1px solid var(--rule-strong);
		border-radius: 3px;
		background: var(--bg);
		color: var(--ink);
		min-width: 15rem;
	}

	.active-context {
		font-size: 0.9rem;
		color: var(--ink-soft);
		margin: 0 0 0.5rem;
	}
	.active-context strong {
		color: var(--ink);
	}
	.region-note {
		font-size: 0.82rem;
		line-height: 1.5;
		color: var(--muted);
		background: var(--bg-panel);
		border-left: 3px solid var(--accent);
		padding: 0.5rem 0.75rem;
		margin: 0 0 1rem;
		border-radius: 0 4px 4px 0;
	}

	.chart-grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 1.5rem;
	}
	@media (max-width: 900px) {
		.chart-grid {
			grid-template-columns: 1fr;
		}
	}

	.chart-card {
		margin: 0;
		padding: 0.9rem 1rem 1rem;
		border: 1px solid var(--rule);
		border-radius: 8px;
		background: var(--bg);
		min-width: 0;
	}
	.chart-title {
		font-family: var(--font-serif);
		font-size: 1.05rem;
		font-weight: 600;
		color: var(--ink);
		margin: 0 0 0.4rem;
	}
	.chart-sub {
		font-size: 0.78rem;
		color: var(--muted);
		margin: 0.4rem 0 0;
		font-variant-numeric: tabular-nums;
	}

	.footnote {
		margin-top: 1.5rem;
		font-size: 0.78rem;
		line-height: 1.55;
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
