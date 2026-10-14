<!--
	TableHeterogeneity — Table 2: "Heterogeneity in Socioeconomic Rank of Fathers of Nobel Laureates"

	Why this file exists:
	    Renders the group-mean comparisons from heterogeneity_spec.json as a
	    three-panel HTML table (Panel A: Gender, Panel B: Prize Category,
	    Panel C: Region). Each cell shows mean (SE) for the group on a given
	    rank outcome, with a p-value row testing equality across groups.

	Upstream dependency: $nobel/data (heterogeneitySpecData from heterogeneity_spec.json)
-->
<script lang="ts">
	import { heterogeneitySpecData, type GroupStats } from '$nobel/data';
	import { replicationSourceUrl } from '$lib/reading/replicationSource';
	import BrandedFrame from '$lib/reading/BrandedFrame.svelte';

	let { number, caption }: { number?: string; caption?: string | null } = $props();

	const d = heterogeneitySpecData;
	const labels = d.meta.labels;

	// Outcomes shown as columns in the table
	const OUTCOME_COLS = [
		{ key: 'med_inctot_rank', short: 'Natl. income rank' },
		{ key: 'educ_rank', short: 'Education rank' },
		{ key: 'global_med_inctot_rank', short: 'Global income rank' },
		{ key: 'top_decile_med_inctot', short: 'Top decile (income)' },
		{ key: 'top_decile_educ', short: 'Top decile (educ.)' }
	];

	type Panel = { title: string; panelKey: 'gender' | 'prize_category' | 'region'; groupKeys: string[]; groupLabels: Record<string, string> };

	const PANELS: Panel[] = [
		{
			title: 'A. Gender',
			panelKey: 'gender',
			groupKeys: ['0', '1'],
			groupLabels: { '0': 'Female', '1': 'Male' }
		},
		{
			title: 'B. Prize Category',
			panelKey: 'prize_category',
			groupKeys: ['1', '2', '3', '4'],
			groupLabels: labels.prize_category
		},
		{
			title: 'C. Region',
			panelKey: 'region',
			groupKeys: ['1', '2', '3', '4', '5'],
			groupLabels: labels.region
		}
	];

	function getGroupStats(outcomeKey: string, panelKey: string, groupKey: string): GroupStats | null {
		const outcome = d.data[outcomeKey] as unknown as Record<string, Record<string, unknown>>;
		const panel = outcome[panelKey];
		const entry = panel?.[groupKey];
		if (!entry || typeof entry !== 'object' || !('mean' in entry)) return null;
		return entry as GroupStats;
	}

	function getPEqual(outcomeKey: string, panelKey: string): number | null {
		const outcome = d.data[outcomeKey] as unknown as Record<string, Record<string, unknown>>;
		const panel = outcome[panelKey];
		const p = panel?.['p_equal'];
		return typeof p === 'number' ? p : null;
	}

	function fmtMean(v: GroupStats, isShare: boolean): string {
		return isShare ? (v.mean * 100).toFixed(1) + '%' : v.mean.toFixed(1);
	}

	function fmtSE(v: GroupStats, isShare: boolean): string {
		return '(' + (isShare ? (v.se * 100).toFixed(1) : v.se.toFixed(1)) + ')';
	}

	function fmtP(p: number | null): string {
		if (p === null) return '';
		if (p < 0.001) return '<0.001';
		return p.toFixed(3);
	}

	function isShareOutcome(key: string): boolean {
		return key.startsWith('top_') || key.startsWith('low');
	}
</script>

<figure class="viz-figure">
	<BrandedFrame
		label={number ? `Table ${number}` : undefined}
		title={caption ?? undefined}
		subtitle="Group means by gender, prize category, and region"
		source="heterogeneity_spec/heterogeneity_spec.py"
		sourceUrl={replicationSourceUrl('heterogeneity_spec/heterogeneity_spec.py')}
	>
		<div class="table-scroll ui">
			<table class="hetero-table">
				<thead>
					<tr>
						<th class="col-group">Group</th>
						<th class="col-n">N</th>
						{#each OUTCOME_COLS as col (col.key)}
							<th class="col-outcome">{col.short}</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each PANELS as panel (panel.panelKey)}
						<tr class="panel-header">
							<td colspan={2 + OUTCOME_COLS.length}>{panel.title}</td>
						</tr>
						{#each panel.groupKeys as gk (gk)}
							{@const firstStats = getGroupStats(OUTCOME_COLS[0].key, panel.panelKey, gk)}
							<tr>
								<td class="col-group">{panel.groupLabels[gk] ?? gk}</td>
								<td class="col-n numeric">{firstStats?.n ?? '—'}</td>
								{#each OUTCOME_COLS as col (col.key)}
									{@const stats = getGroupStats(col.key, panel.panelKey, gk)}
									<td class="col-outcome numeric">
										{#if stats}
											<span class="mean">{fmtMean(stats, isShareOutcome(col.key))}</span>
											<span class="se">{fmtSE(stats, isShareOutcome(col.key))}</span>
										{:else}
											<span class="muted">—</span>
										{/if}
									</td>
								{/each}
							</tr>
						{/each}
						<tr class="p-equal-row">
							<td class="col-group label-muted" colspan="2">p-value (equal)</td>
							{#each OUTCOME_COLS as col (col.key)}
								<td class="col-outcome numeric label-muted">
									{fmtP(getPEqual(col.key, panel.panelKey))}
								</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
			<p class="table-note">
				Group means with robust standard errors in parentheses. Rank outcomes
				are on a 0–100 scale; top-decile outcomes are shown as percentages. p-value tests equality of
				means across groups using a Wald F-test.
			</p>
		</div>
	</BrandedFrame>
</figure>

<style>
	.viz-figure {
		margin: 2rem 0;
		font-family: var(--font-ui);
	}

	.table-scroll {
		overflow-x: auto;
	}

	.hetero-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.82rem;
		line-height: 1.4;
		table-layout: fixed;
	}

	.hetero-table thead th {
		text-align: right;
		font-weight: 600;
		font-size: 0.74rem;
		padding: 0.4rem 0.4rem;
		border-bottom: 2px solid var(--ink);
		/* Wrap header labels onto 2–3 lines rather than forcing wide columns —
		   this is what lets the 7-column table fit the reading measure without
		   a horizontal scrollbar. */
		white-space: normal;
		hyphens: auto;
		vertical-align: bottom;
	}

	.hetero-table thead th.col-group {
		text-align: left;
	}

	.hetero-table tbody tr:not(.panel-header):not(.p-equal-row) td {
		padding: 0.3rem 0.4rem;
		border-bottom: 1px solid var(--rule);
	}

	.hetero-table tbody tr:not(.panel-header):not(.p-equal-row):hover td {
		background: var(--bg-panel);
	}

	.panel-header td {
		padding: 0.85rem 0.4rem 0.2rem;
		font-weight: 700;
		font-size: 0.8rem;
		letter-spacing: 0.02em;
		color: var(--ink);
		border-top: 2px solid var(--ink);
		text-transform: uppercase;
	}

	.panel-header:first-child td {
		border-top: none;
		padding-top: 0.4rem;
	}

	.p-equal-row td {
		padding: 0.25rem 0.4rem 0.65rem;
		border-bottom: 1px solid var(--rule-strong);
	}

	.col-group {
		font-weight: 500;
		width: 15%;
		white-space: normal;
	}

	.col-n,
	.col-outcome {
		text-align: right;
		white-space: nowrap;
	}

	.col-n {
		width: 6%;
	}

	.col-outcome {
		width: calc((100% - 21%) / 5);
	}

	.numeric {
		font-variant-numeric: tabular-nums;
	}

	.mean {
		display: block;
		font-weight: 500;
	}

	.se {
		display: block;
		font-size: 0.8rem;
		color: var(--muted);
	}

	.label-muted {
		color: var(--muted);
		font-size: 0.82rem;
	}

	.muted {
		color: var(--muted);
	}

	.table-note {
		margin-top: 0.75rem;
		font-size: 0.8rem;
		color: var(--muted);
		line-height: 1.5;
	}
</style>
