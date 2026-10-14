<!--
	AppendixTable — generic renderer for the appendix tables shown in the
	right-hand "Additional Information" pane.

	Why this file exists:
	    The ~7 appendix tables share one presentation (a compact, optionally
	    scrollable HTML table inside a BrandedFrame) but come from differently
	    shaped data. This component renders any of them from a single
	    `AppendixTableSpec`; the per-table data-shaping lives in
	    `appendixTables.ts`. It is registered once in `appendixRegistry` and
	    selected via the `table` prop supplied by the content JSON, so adding a
	    table needs only a new spec + a content annotation, not a new component.

	Props:
	    - table: the table id passed to `getAppendixTable` (e.g. "occ_shares_10").
	    - hideHeading, hideNote: omit repeated copy when the popup supplies it.

	Upstream dependencies:
	    ./appendixTables (getAppendixTable), ./BrandedFrame
-->
<script lang="ts">
	import BrandedFrame from '$lib/reading/BrandedFrame.svelte';
	import { getAppendixTable, type TableCell } from './appendixTables';

	let { table, hideHeading = false, hideNote = false }: {
		table: string;
		hideHeading?: boolean;
		hideNote?: boolean;
	} = $props();

	const spec = $derived(getAppendixTable(table));

	/** Normalise a cell (string or {main, sub}) to the object form. */
	function cell(v: TableCell | string): TableCell {
		return typeof v === 'string' ? { main: v } : v;
	}
</script>

{#if spec}
	<figure class="viz-figure">
		<BrandedFrame
			label={hideHeading ? undefined : spec.title}
			title={undefined}
			subtitle={hideHeading ? undefined : spec.subtitle}
			source={spec.source}
			sourceUrl={spec.sourceUrl}
		>
			<div class="table-scroll ui" class:scroll-y={spec.scrollY}>
				<table class="appendix-table" class:compact={spec.compact}>
					<thead>
						<tr>
							<th class="col-label">{spec.rowLabelHeader}</th>
							{#each spec.columns as col (col.key)}
								<th class="col-val" class:text-column={col.text}>
									{col.label}
									{#if col.sublabel}<span class="col-unit">{col.sublabel}</span>{/if}
								</th>
							{/each}
						</tr>
					</thead>
					<tbody>
						{#each spec.groups as group, gi (gi)}
							{#if group.label}
								<tr class="group-header">
									<td colspan={spec.columns.length + 1}>{group.label}</td>
								</tr>
							{/if}
							{#each group.rows as row, ri (ri)}
								<tr class:muted-row={row.muted}>
									<td class="col-label">{row.label}</td>
									{#each spec.columns as col (col.key)}
										{@const c = cell(row.cells[col.key] ?? '—')}
									<td class="col-val numeric" class:text-column={col.text}>
											<span class="cell-main">{c.main}</span>
											{#if c.sub}<span class="cell-sub">{c.sub}</span>{/if}
										</td>
									{/each}
								</tr>
							{/each}
						{/each}
					</tbody>
				</table>
			</div>
			{#if !hideNote}
				{#if spec.significanceLegend}
					<p class="table-note">{spec.significanceLegend}</p>
				{/if}
				{#if spec.note}<p class="table-note">{spec.note}</p>{/if}
			{/if}
		</BrandedFrame>
	</figure>
{:else}
	<p class="table-missing">Table data unavailable (unknown table “{table}”).</p>
{/if}

<style>
	.viz-figure {
		margin: 0;
		font-family: var(--font-ui);
	}

	.table-scroll {
		overflow-x: auto;
	}

	/* Long reference tables (269-row crosswalks) get a capped, scrollable body
	   so the pane stays navigable. */
	.table-scroll.scroll-y {
		max-height: 55vh;
		overflow-y: auto;
	}

	.appendix-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.8rem;
		line-height: 1.4;
	}

	.appendix-table thead th {
		position: sticky;
		top: 0;
		z-index: 1;
		background: var(--bg, #fff);
		text-align: right;
		font-weight: 600;
		font-size: 0.72rem;
		padding: 0.35rem 0.5rem;
		border-bottom: 2px solid var(--ink);
		white-space: nowrap;
		vertical-align: bottom;
	}

	.appendix-table thead th.col-label {
		text-align: left;
	}

	.col-unit {
		display: block;
		font-weight: 400;
		font-size: 0.66rem;
		color: var(--muted);
	}

	.appendix-table tbody td {
		padding: 0.28rem 0.5rem;
		border-bottom: 1px solid var(--rule);
		vertical-align: top;
	}

	.appendix-table tbody tr:not(.group-header):not(.muted-row):hover td {
		background: var(--bg-panel);
	}

	.col-label {
		text-align: left;
		font-weight: 500;
		min-width: 90px;
	}

	.col-val {
		text-align: right;
		white-space: nowrap;
	}

	.numeric {
		font-variant-numeric: tabular-nums;
	}

	.appendix-table .text-column {
		text-align: left;
		white-space: normal;
		overflow-wrap: anywhere;
	}

	.compact .col-label {
		min-width: 0;
	}

	.appendix-table.compact th,
	.appendix-table.compact td {
		padding-inline: 0.3rem;
	}

	.cell-main {
		display: block;
	}

	.cell-sub {
		display: block;
		font-size: 0.72rem;
		color: var(--muted);
	}

	.group-header td {
		padding: 0.7rem 0.5rem 0.2rem;
		font-weight: 700;
		font-size: 0.72rem;
		letter-spacing: 0.02em;
		text-transform: uppercase;
		color: var(--ink);
		border-top: 2px solid var(--ink);
		border-bottom: none;
	}

	.muted-row td {
		color: var(--muted);
		font-size: 0.74rem;
		border-bottom: 1px solid var(--rule-strong);
	}

	.table-note {
		margin: 0.7rem 0 0;
		font-size: 0.74rem;
		color: var(--muted);
		line-height: 1.5;
	}

	.table-missing {
		font-size: 0.78rem;
		font-style: italic;
		color: var(--muted);
	}
</style>
