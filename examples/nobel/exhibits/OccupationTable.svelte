<!--
	OccupationTable — the complete occupation representation table for the
	Occupation Explorer page.

	For a chosen classification level (10 broad groups / 25-group / all detailed
	occupations) it lists, per occupation, how over-represented laureates' fathers
	are: laureate-father count, expected fathers under the population share, the
	weighted-average income and education ranks, prize share, census share, and the
	over-representation ratio. A search box filters by label/code; every column is
	sortable (ascending → descending → natural, nulls sink), and the list paginates
	client-side — the sort/search/paginate behavior mirrors NobelistsDataTable.

	Why the three levels feed one table: the site already ships the three
	occ_shares JSON datasets; this component normalizes them into one row shape
	rather than duplicating their values in a new file. Table averages weight
	country–decade cells to match where/when laureates were born, so they are NOT
	U.S.-only and need not equal the rank chart's U.S. trajectories.

	Upstream dependencies:
	  - $nobel/data (occShares10Data, occShares25Data, occShares1950ListData; types)
-->
<script lang="ts">
	import {
		occShares10Data,
		occShares25Data,
		occShares1950ListData,
		type OccShareGroupRow,
		type Occ1950Row
	} from '$nobel/data';

	type LevelId = 'occgroup_10' | 'occgroup_25' | 'occ1950';
	const LEVELS: { id: LevelId; label: string }[] = [
		{ id: 'occgroup_10', label: '10 broad groups' },
		{ id: 'occgroup_25', label: '25-group classification' },
		{ id: 'occ1950', label: 'All occupations' }
	];

	// One normalized row. `occCount` is null for detailed occupations (the
	// "Occupations" column is hidden at that level).
	interface Row {
		id: string;
		label: string;
		occCount: number | null;
		laureateN: number;
		expectedFathers: number;
		incomeRank: number | null;
		educRank: number | null;
		prizePct: number;
		censusPct: number;
		overrep: number | null;
	}

	// Sum detailed laureate_n (currently 703). Derived, not hardcoded, for
	// expected_fathers = census_share * total.
	const laureateTotal = occShares1950ListData.data.reduce((s, r) => s + r.laureate_n, 0);

	function grpRow(r: OccShareGroupRow, i: number): Row {
		return {
			id: `g${i}`,
			label: r.label,
			occCount: r.occ_count,
			laureateN: r.laureate_n,
			expectedFathers: r.census_share * laureateTotal,
			incomeRank: r.avg_med_inctot_rank ?? null,
			educRank: r.avg_educ_rank ?? null,
			prizePct: r.laureate_pct,
			censusPct: r.census_pct,
			overrep: r.overrep_ratio ?? null
		};
	}
	function detRow(r: Occ1950Row): Row {
		return {
			id: `d${r.occ1950}`,
			label: r.display,
			occCount: null,
			laureateN: r.laureate_n,
			expectedFathers: r.census_share * laureateTotal,
			incomeRank: r.med_inctot_rank ?? null,
			educRank: r.educ_rank ?? null,
			prizePct: r.laureate_pct,
			censusPct: r.census_pct,
			overrep: r.overrep_ratio ?? null
		};
	}

	// Preserve delivered array order — it IS the pipeline's classification order.
	const ROWS: Record<LevelId, Row[]> = {
		occgroup_10: occShares10Data.data.map(grpRow),
		occgroup_25: occShares25Data.data.map(grpRow),
		occ1950: occShares1950ListData.data.map(detRow)
	};

	let levelId = $state<LevelId>('occgroup_10');
	let search = $state('');

	type SortKey =
		| 'label'
		| 'occCount'
		| 'laureateN'
		| 'expectedFathers'
		| 'incomeRank'
		| 'educRank'
		| 'prizePct'
		| 'censusPct'
		| 'overrep';
	let sortKey = $state<SortKey | null>(null);
	let sortDir = $state<'asc' | 'desc'>('asc');

	const pageSizes = [25, 50, 100, 250];
	let pageSize = $state(50);
	let page = $state(1);

	function onLevelChange() {
		page = 1;
	}
	function onSearch() {
		page = 1;
	}
	function changePageSize(e: Event) {
		pageSize = Number((e.currentTarget as HTMLSelectElement).value);
		page = 1;
	}

	function sortBy(key: SortKey) {
		if (sortKey !== key) {
			sortKey = key;
			sortDir = 'asc';
		} else if (sortDir === 'asc') {
			sortDir = 'desc';
		} else {
			sortKey = null;
			sortDir = 'asc';
		}
		page = 1;
	}
	function ariaSort(key: SortKey): 'ascending' | 'descending' | 'none' {
		if (sortKey !== key) return 'none';
		return sortDir === 'asc' ? 'ascending' : 'descending';
	}

	const baseRows = $derived(ROWS[levelId]);
	const isDetailed = $derived(levelId === 'occ1950');

	const filtered = $derived.by(() => {
		const q = search.trim().toLowerCase();
		if (!q) return baseRows;
		return baseRows.filter((r) => r.label.toLowerCase().includes(q));
	});

	const sorted = $derived.by(() => {
		if (sortKey == null) return filtered;
		const key = sortKey;
		const dir = sortDir === 'asc' ? 1 : -1;
		return [...filtered].sort((a, b) => {
			const av = a[key];
			const bv = b[key];
			const aE = av == null || av === '';
			const bE = bv == null || bv === '';
			if (aE && bE) return 0;
			if (aE) return 1;
			if (bE) return -1;
			const cmp =
				typeof av === 'number' && typeof bv === 'number'
					? av - bv
					: String(av).localeCompare(String(bv));
			return cmp * dir;
		});
	});

	const total = $derived(sorted.length);
	const totalPages = $derived(Math.max(1, Math.ceil(total / pageSize)));
	const start = $derived((page - 1) * pageSize);
	const paged = $derived(sorted.slice(start, start + pageSize));
	const rangeStart = $derived(total === 0 ? 0 : start + 1);
	const rangeEnd = $derived(Math.min(start + pageSize, total));
	$effect(() => {
		if (page > totalPages) page = totalPages;
	});

	function goTo(p: number) {
		page = Math.min(Math.max(1, p), totalPages);
	}

	// --- Formatting ---
	function fmtRank(v: number | null): string {
		return v == null ? '—' : v.toFixed(1);
	}
	function fmtInt(v: number | null): string {
		return v == null ? '—' : String(v);
	}
	function fmtOneDp(v: number | null): string {
		return v == null ? '—' : v.toFixed(1);
	}
	function fmtPct(v: number | null): string {
		if (v == null) return '—';
		return v >= 1 ? v.toFixed(1) : v.toFixed(2);
	}
	function fmtOverrep(v: number | null): string {
		if (v == null) return '—';
		return v < 1 ? `${v.toFixed(2)}×` : `${v.toFixed(1)}×`;
	}
	function isHigh(v: number | null): boolean {
		return v != null && v > 80;
	}

	// Columns present at every level; "Occupations" is dropped for detailed rows.
	type Col = { key: SortKey; label: string; num: boolean; groupedOnly?: boolean };
	const columns: Col[] = [
		{ key: 'label', label: 'Group / Occupation', num: false },
		{ key: 'occCount', label: 'Occupations', num: true, groupedOnly: true },
		{ key: 'laureateN', label: 'Laureate fathers', num: true },
		{ key: 'expectedFathers', label: 'Expected fathers', num: true },
		{ key: 'incomeRank', label: 'Weighted avg. income rank', num: true },
		{ key: 'educRank', label: 'Weighted avg. education rank', num: true },
		{ key: 'prizePct', label: 'Prize share', num: true },
		{ key: 'censusPct', label: 'Census share', num: true },
		{ key: 'overrep', label: 'Over-representation', num: true }
	];
	const shownColumns = $derived(columns.filter((c) => !c.groupedOnly || !isDetailed));
</script>

<div class="occ-table-controls ui">
	<label class="ctl">
		<span>Classification</span>
		<select bind:value={levelId} onchange={onLevelChange}>
			{#each LEVELS as lvl (lvl.id)}
				<option value={lvl.id}>{lvl.label}</option>
			{/each}
		</select>
	</label>
	<label class="ctl search">
		<span>Search occupations</span>
		<input type="search" placeholder="Filter by name…" bind:value={search} oninput={onSearch} />
	</label>
	<p class="count" aria-live="polite">{total.toLocaleString()} rows</p>
</div>

<div class="table-wrap">
	<table class="ui data-table">
		<caption class="sr-only">Occupation representation of Nobel laureates' fathers</caption>
		<thead>
			<tr>
				{#each shownColumns as col (col.key)}
					<th scope="col" class:num={col.num} class="sortable" aria-sort={ariaSort(col.key)}>
						<button
							type="button"
							class="sort-btn"
							class:active={sortKey === col.key}
							onclick={() => sortBy(col.key)}
						>
							<span class="sort-label">{col.label}</span>
							<span class="sort-ind" aria-hidden="true"
								>{#if sortKey === col.key}{sortDir === 'asc' ? '▲' : '▼'}{/if}</span
							>
						</button>
					</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each paged as row (row.id)}
				<tr class:high-row={isHigh(row.incomeRank) || isHigh(row.educRank)}>
					<th scope="row" class="col-label">{row.label}</th>
					{#if !isDetailed}
						<td class="num">{fmtInt(row.occCount)}</td>
					{/if}
					<td class="num">{fmtInt(row.laureateN)}</td>
					<td class="num">{fmtOneDp(row.expectedFathers)}</td>
					<td class="num rank" class:high-cell={isHigh(row.incomeRank)}>{fmtRank(row.incomeRank)}</td
					>
					<td class="num rank" class:high-cell={isHigh(row.educRank)}>{fmtRank(row.educRank)}</td>
					<td class="num">{fmtPct(row.prizePct)}</td>
					<td class="num">{fmtPct(row.censusPct)}</td>
					<td class="num">{fmtOverrep(row.overrep)}</td>
				</tr>
			{/each}
			{#if total === 0}
				<tr><td class="empty" colspan={shownColumns.length}>No occupations match “{search}”.</td></tr>
			{/if}
		</tbody>
	</table>
</div>

<nav class="pager ui" aria-label="Table pagination">
	<span class="range"
		>{rangeStart.toLocaleString()}–{rangeEnd.toLocaleString()} of {total.toLocaleString()}</span
	>
	<label class="page-size">
		Rows
		<select value={pageSize} onchange={changePageSize}>
			{#each pageSizes as size (size)}<option value={size}>{size}</option>{/each}
		</select>
	</label>
	<div class="pager-controls">
		<button type="button" onclick={() => goTo(1)} disabled={page <= 1} aria-label="First page">«</button
		>
		<button type="button" onclick={() => goTo(page - 1)} disabled={page <= 1} aria-label="Previous page"
			>‹</button
		>
		<span class="page-of">Page {page} of {totalPages}</span>
		<button
			type="button"
			onclick={() => goTo(page + 1)}
			disabled={page >= totalPages}
			aria-label="Next page">›</button
		>
		<button
			type="button"
			onclick={() => goTo(totalPages)}
			disabled={page >= totalPages}
			aria-label="Last page">»</button
		>
	</div>
</nav>

<style>
	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0 0 0 0);
		white-space: nowrap;
		border: 0;
	}
	.occ-table-controls {
		display: flex;
		flex-wrap: wrap;
		align-items: flex-end;
		gap: 0.75rem 1.25rem;
		margin-bottom: 0.85rem;
	}
	.ctl {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		font-size: 0.78rem;
		color: var(--muted);
	}
	.ctl > span {
		font-weight: 600;
		letter-spacing: 0.02em;
	}
	.ctl select,
	.ctl input {
		font-family: var(--font-ui);
		font-size: 0.85rem;
		color: var(--ink);
		padding: 0.35rem 0.6rem;
		border: 1px solid var(--rule-strong, #ccc);
		border-radius: var(--ddl-border-radius, 4px);
		background: var(--bg, #fff);
	}
	.ctl.search input {
		min-width: 16rem;
	}
	.ctl select:focus-visible,
	.ctl input:focus-visible {
		outline: 2px solid var(--accent);
		outline-offset: 1px;
	}
	.count {
		margin: 0 0 0 auto;
		font-size: 0.8rem;
		color: var(--muted);
	}

	.table-wrap {
		overflow: auto;
		max-height: 60vh;
		border: 1px solid var(--rule);
		border-radius: 8px;
		background: var(--bg);
	}
	.data-table {
		border-collapse: separate;
		border-spacing: 0;
		width: 100%;
		font-size: 0.82rem;
		line-height: 1.35;
		color: var(--ink-soft);
	}
	thead th {
		position: sticky;
		top: 0;
		z-index: 1;
		background: var(--bg-panel);
		text-align: left;
		font-weight: 600;
		font-size: 0.72rem;
		letter-spacing: 0.02em;
		color: var(--ink);
		padding: 0;
		border-bottom: 1px solid var(--rule-strong);
	}
	thead th.num {
		text-align: right;
	}
	.sort-btn {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		width: 100%;
		font: inherit;
		font-weight: inherit;
		letter-spacing: inherit;
		color: inherit;
		background: none;
		border: 0;
		padding: 0.6rem 0.75rem;
		cursor: pointer;
		text-align: left;
	}
	th.num .sort-btn {
		justify-content: flex-end;
		text-align: right;
	}
	.sort-btn:hover,
	.sort-btn.active {
		color: var(--accent);
	}
	.sort-btn:focus-visible {
		outline: 2px solid var(--accent);
		outline-offset: -2px;
	}
	.sort-ind {
		min-width: 0.75em;
		font-size: 0.7em;
		line-height: 1;
		flex-shrink: 0;
	}

	tbody th,
	tbody td {
		padding: 0.5rem 0.75rem;
		border-bottom: 1px solid var(--rule);
		vertical-align: top;
	}
	.col-label {
		font-weight: 600;
		color: var(--ink);
		min-width: 14rem;
	}
	tbody tr:nth-child(even) th,
	tbody tr:nth-child(even) td {
		background: color-mix(in srgb, var(--bg-panel) 55%, transparent);
	}
	tbody tr:hover th,
	tbody tr:hover td {
		background: color-mix(in srgb, var(--accent) 7%, transparent);
	}

	/* A row with either weighted rank above 80 is highlighted subtly; the
	   above-80 rank cell itself gets a stronger tint. Threshold is strictly > 80. */
	tbody tr.high-row th,
	tbody tr.high-row td {
		background: color-mix(in srgb, var(--accent) 5%, transparent);
	}
	.high-cell {
		background: color-mix(in srgb, var(--accent) 14%, transparent) !important;
		font-weight: 600;
		color: var(--ink);
	}

	.num {
		text-align: right;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	.rank {
		color: var(--ink-soft);
	}
	.empty {
		text-align: center;
		color: var(--muted);
		padding: 1.5rem;
	}

	.pager {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.75rem 1.25rem;
		margin-top: 0.85rem;
		font-size: 0.8rem;
		color: var(--muted);
	}
	.range {
		font-variant-numeric: tabular-nums;
	}
	.page-size {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
	}
	.page-size select {
		font: inherit;
		color: var(--ink-soft);
		background: var(--bg);
		border: 1px solid var(--rule-strong);
		border-radius: 5px;
		padding: 0.15rem 0.35rem;
		cursor: pointer;
	}
	.pager-controls {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		margin-left: auto;
	}
	.page-of {
		font-variant-numeric: tabular-nums;
		padding: 0 0.4rem;
		white-space: nowrap;
	}
	.pager-controls button {
		font: inherit;
		line-height: 1;
		color: var(--ink-soft);
		background: var(--bg);
		border: 1px solid var(--rule-strong);
		border-radius: 5px;
		min-width: 1.9rem;
		padding: 0.25rem 0.4rem;
		cursor: pointer;
	}
	.pager-controls button:hover:not(:disabled) {
		border-color: var(--accent);
		color: var(--accent);
	}
	.pager-controls button:disabled {
		opacity: 0.4;
		cursor: default;
	}
</style>
