<!--
	TableMainSpec — Table 1: "Secular Trends in Socioeconomic Ranks of Fathers of Nobel Laureates"

	Why this file exists:
	    Renders the OLS regression results from main_spec.json as an interactive
	    HTML table. Each row shows one outcome variable, its trend coefficient (and
	    SE), the sample size, and sample mean. The coefficient is expressed per 100 prize
	    years for interpretability. Grouped into rank outcomes and bottom-percentile
	    share outcomes.

	Upstream dependency: $nobel/data (mainSpecData from main_spec.json)
-->
<script lang="ts">
	import { mainSpecData } from '$nobel/data';
	import { replicationSourceUrl } from '$lib/reading/replicationSource';
	import BrandedFrame from '$lib/reading/BrandedFrame.svelte';

	let { number, caption }: { number?: string; caption?: string | null } = $props();

	const RANK_KEYS = ['med_inctot_rank', 'educ_rank', 'global_med_inctot_rank'];
	const BOTTOM90_KEYS = ['low90_inc', 'low90_educ', 'low90_glo'];
	const BOTTOM80_KEYS = ['low80_inc', 'low80_educ', 'low80_glo'];

	const rows = mainSpecData.data;

	function stars(coef: number, se: number): string {
		const t = Math.abs(coef / se);
		if (t > 2.576) return '***';
		if (t > 1.96) return '**';
		if (t > 1.645) return '*';
		return '';
	}

	// Coefficient × 100 = change per 100 prize years
	function fmt100(coef: number, se: number): string {
		const val = (coef * 100).toFixed(3);
		return val + stars(coef, se);
	}

	function fmtSE(se: number): string {
		return '(' + (se * 100).toFixed(3) + ')';
	}

	const groups = [
		{
			header: 'Dependent variable: Father rank (0–100)',
			note: 'Higher rank = higher SES. Unit: rank points per 100 prize years.',
			keys: RANK_KEYS
		},
		{
			header: 'Dependent variable: Share from bottom 90%',
			note: 'Fraction of laureates with fathers below the 90th percentile.',
			keys: BOTTOM90_KEYS
		},
		{
			header: 'Dependent variable: Share from bottom 80%',
			note: 'Fraction of laureates with fathers below the 80th percentile.',
			keys: BOTTOM80_KEYS
		}
	];
</script>

<figure class="viz-figure">
	<BrandedFrame
		label={number ? `Table ${number}` : undefined}
		title={caption ?? undefined}
		source="main_spec/main_spec.py"
		sourceUrl={replicationSourceUrl('main_spec/main_spec.py')}
	>
		<div class="table-scroll ui">
			<table class="spec-table">
				<thead>
					<tr>
						<th class="col-outcome">Outcome variable</th>
						<th class="col-est" title="OLS coefficient × 100 (change per 100 prize years). Stars: * p&lt;0.10, ** p&lt;0.05, *** p&lt;0.01">
							Estimate<br /><span class="col-unit">(per 100 yrs)</span>
						</th>
						<th class="col-n">N</th>
						<th class="col-mean">Sample mean</th>
					</tr>
				</thead>
				<tbody>
					{#each groups as group (group.header)}
						<tr class="group-header">
							<td colspan="4">
								<span class="group-title">{group.header}</span>
								<span class="group-note">{group.note}</span>
							</td>
						</tr>
						{#each group.keys as key (key)}
							{@const row = rows[key]}
							<tr>
								<td class="col-outcome">{row.label}</td>
								<td class="col-est numeric">
									<span class="coef">{fmt100(row.coef, row.se)}</span>
									<span class="se">{fmtSE(row.se)}</span>
								</td>
								<td class="col-n numeric">{row.n}</td>
								<td class="col-mean numeric">{row.sample_mean.toFixed(3)}</td>
							</tr>
						{/each}
					{/each}
				</tbody>
			</table>
			<p class="table-note">
				OLS regression of each outcome on prize year (rescaled to 0 in 1901). Robust standard
				errors in parentheses. Estimate expressed as change per 100 prize years for interpretability.
				* p&lt;0.10, ** p&lt;0.05, *** p&lt;0.01.
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

	.spec-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.82rem;
		line-height: 1.45;
	}

	.spec-table thead th {
		text-align: left;
		font-weight: 600;
		font-size: 0.74rem;
		letter-spacing: 0.02em;
		color: var(--ink);
		padding: 0.45rem 0.75rem;
		border-bottom: 2px solid var(--ink);
		white-space: nowrap;
		vertical-align: bottom;
	}

	.col-unit {
		font-weight: 400;
		font-size: 0.75rem;
		color: var(--muted);
	}

	.spec-table tbody tr:not(.group-header) td {
		padding: 0.35rem 0.75rem;
		border-bottom: 1px solid var(--rule);
		color: var(--ink);
	}

	.spec-table tbody tr:not(.group-header):hover td {
		background: var(--bg-panel);
	}

	.group-header td {
		padding: 1rem 0.75rem 0.2rem;
		border-top: 1px solid var(--rule-strong);
		background: transparent;
	}

	.group-header:first-child td {
		border-top: none;
		padding-top: 0.5rem;
	}

	.group-title {
		display: block;
		font-weight: 600;
		font-size: 0.8rem;
		color: var(--ink);
		letter-spacing: 0.01em;
	}

	.group-note {
		display: block;
		font-size: 0.75rem;
		color: var(--muted);
		margin-top: 0.1rem;
	}

	.col-outcome {
		max-width: 260px;
	}

	.col-est,
	.col-n,
	.col-mean {
		white-space: nowrap;
		text-align: right;
	}

	thead .col-est,
	thead .col-n,
	thead .col-mean {
		text-align: right;
	}

	.numeric {
		font-variant-numeric: tabular-nums;
		font-family: var(--font-ui);
	}

	.coef {
		display: block;
		font-weight: 500;
	}

	.se {
		display: block;
		color: var(--muted);
		font-size: 0.82rem;
	}

	.table-note {
		margin-top: 0.75rem;
		font-size: 0.8rem;
		color: var(--muted);
		line-height: 1.5;
	}
</style>
