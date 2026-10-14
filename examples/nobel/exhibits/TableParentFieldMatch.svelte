<!--
	TableParentFieldMatch — Table 3: "Parent-Child Field Match Randomization Tests"

	Why this file exists:
	    Renders the parent-child field match summary statistics from
	    parent_field_match_shares.json as an HTML table. Shows the observed
	    parent-child field match share vs. the expected share under random
	    assignment, along with the excess rate and randomization-test p-value.
	    Rows = match-quality tier (primary, professor subset, non-professor subset,
	    secondary/weak). Columns = non-econ sample | econ sample.

	Upstream dependency: $nobel/data (matchSharesData from parent_field_match_shares.json)
-->
<script lang="ts">
	import { permTestData } from '$nobel/data';
	import { replicationSourceUrl } from '$lib/reading/replicationSource';
	import BrandedFrame from '$lib/reading/BrandedFrame.svelte';

	let { number, caption }: { number?: string; caption?: string | null } = $props();

	const d = permTestData.data;

	type RowSpec = { label: string; desc: string; nonEconKey: string; econKey: string };

	const ROWS: RowSpec[] = [
		{
			label: 'Primary field match',
			desc: 'All parents with an occupation directly linked to a Nobel field',
			nonEconKey: 'good_nonecon_sample',
			econKey: 'good_econ_sample'
		},
		{
			label: '— Professors only',
			desc: 'Subset: fathers who were professors',
			nonEconKey: 'prof_match_nonecon_sample',
			econKey: 'prof_match_econ_sample'
		},
		{
			label: '— Non-professors',
			desc: 'Subset: fathers in a field-linked occupation other than professor',
			nonEconKey: 'nonprof_match_nonecon_sample',
			econKey: 'nonprof_match_econ_sample'
		},
		{
			label: 'Secondary/weak match',
			desc: 'Broader classification with indirect topical links to a Nobel field',
			nonEconKey: 'weak_match_nonecon_sample',
			econKey: 'weak_match_econ_sample'
		}
	];

	function fmtPct(v: number): string {
		return v.toFixed(1) + '%';
	}

	function fmtExcess(v: number): string {
		return (v > 0 ? '+' : '') + v.toFixed(1) + '%';
	}
</script>

<figure class="viz-figure">
	<BrandedFrame
		label={number ? `Table ${number}` : undefined}
		title={caption ?? undefined}
		subtitle="Observed vs. expected match rates, non-econ and econ samples"
		source="parent_field_match/parent_field_perm_test.py"
		sourceUrl={replicationSourceUrl('parent_field_match/parent_field_perm_test.py')}
	>
		<div class="table-scroll ui">
			<table class="match-table">
				<thead>
					<tr>
						<th class="col-label" rowspan="2">Sample</th>
						<th colspan="5" class="col-group-header">Non-economics sample (Chem/Physics/Medicine)</th>
						<th colspan="5" class="col-group-header">Economics sample (all fields, 1969–)</th>
					</tr>
					<tr>
						<th class="col-num">N</th>
						<th class="col-obs">Observed</th>
						<th class="col-exp">Expected</th>
						<th class="col-exc">Excess</th>
						<th class="col-p">p-value</th>
						<th class="col-num">N</th>
						<th class="col-obs">Observed</th>
						<th class="col-exp">Expected</th>
						<th class="col-exc">Excess</th>
						<th class="col-p">p-value</th>
					</tr>
				</thead>
				<tbody>
					{#each ROWS as row (row.nonEconKey)}
						{@const ne = d[row.nonEconKey]}
						{@const ec = d[row.econKey]}
						<tr class:indent={row.label.startsWith('—')}>
							<td class="col-label">
								<span class="row-label">{row.label}</span>
								<span class="row-desc">{row.desc}</span>
							</td>
							<td class="numeric">{ne.n}</td>
							<td class="numeric">{fmtPct(ne.observed_pct)}</td>
							<td class="numeric">{fmtPct(ne.expected_pct)}</td>
							<td class="numeric excess">{fmtExcess(ne.excess_rate)}</td>
							<td class="numeric">{ne.p_value_display}</td>
							<td class="numeric">{ec.n}</td>
							<td class="numeric">{fmtPct(ec.observed_pct)}</td>
							<td class="numeric">{fmtPct(ec.expected_pct)}</td>
							<td class="numeric excess">{fmtExcess(ec.excess_rate)}</td>
							<td class="numeric">{ec.p_value_display}</td>
						</tr>
					{/each}
				</tbody>
			</table>
			<p class="table-note">
				Randomization test: each simulation randomly assigns laureate children to fields using the
				empirical field distribution. Observed = fraction of parent-child pairs in the same field.
				Expected = mean of 10,000 simulated draws. Excess = (Observed − Expected) / Expected.
				p-value = fraction of simulations with at least as large a match share as observed.
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

	.match-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
		line-height: 1.4;
	}

	.match-table thead th {
		text-align: right;
		font-weight: 600;
		font-size: 0.78rem;
		padding: 0.35rem 0.5rem;
		border-bottom: 1px solid var(--rule-strong);
		white-space: nowrap;
	}

	.match-table thead th.col-label {
		text-align: left;
	}

	.col-group-header {
		border-bottom: 2px solid var(--ink);
		text-align: center !important;
		font-size: 0.77rem;
		letter-spacing: 0.01em;
	}

	.match-table tbody td {
		padding: 0.35rem 0.5rem;
		border-bottom: 1px solid var(--rule);
	}

	.match-table tbody tr:hover td {
		background: var(--bg-panel);
	}

	.indent td.col-label {
		padding-left: 1.25rem;
	}

	.col-label {
		min-width: 200px;
	}

	.row-label {
		display: block;
		font-weight: 500;
		color: var(--ink);
	}

	.row-desc {
		display: block;
		font-size: 0.78rem;
		color: var(--muted);
		margin-top: 0.1rem;
	}

	.col-num,
	.col-obs,
	.col-exp,
	.col-exc,
	.col-p {
		white-space: nowrap;
		min-width: 58px;
	}

	.numeric {
		text-align: right;
		font-variant-numeric: tabular-nums;
	}

	.excess {
		font-weight: 600;
		color: var(--accent);
	}

	.table-note {
		margin-top: 0.75rem;
		font-size: 0.8rem;
		color: var(--muted);
		line-height: 1.5;
	}
</style>
