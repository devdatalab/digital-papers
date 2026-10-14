<!--
	NobelistsDataTable — tabular view of the laureate analysis dataset for the
	Data Explorer (section 7).

	Why it exists: the Data Explorer's first job is to expose the paper's
	underlying per-laureate dataset as a plain, legible table. This component owns
	the column definitions and cell formatting; the page owns the surrounding
	chrome (intro, toolbar, placeholders). Keeping the table here mirrors the
	repo's content/render split and keeps the page component small.

	Columns cover the human-readable identity fields (laureate, prize, year,
	country, gender, award age, father's occupation, plus the occupation a Gemini
	grounded search found) and the three parental background percentile ranks that
	the paper analyses. Rank column headers are sourced from `nobelMetrics` so
	they stay in sync with the dataset; a short label per metric keeps the header
	row compact.

	Each row also has a leading disclosure control: expanding it reveals the
	grounded search's provenance for that laureate — the supporting quote, the
	occupation reasoning, and clickable source links — as a full-width detail
	panel. This keeps the grid scannable while making the evidence trail one click
	away (progressive disclosure, per CLAUDE.md).

	Every column is sortable: clicking a header cycles ascending → descending →
	natural order, with null/blank cells always sinking to the bottom so a sort
	never hides the sparse rows. Sorting happens on a copy of the `rows` prop
	(never mutating it) and feeds pagination below.

	The dataset runs to hundreds of rows, so the table paginates client-side:
	only the current page's rows are rendered, with a footer bar for page size and
	prev/next. Search filters all displayed columns before sorting and pagination,
	and resets the current page whenever the query changes.

	Upstream dependencies:
	  - $nobel/data (NobelRow, Metric types; caller passes the rows + metrics)
-->
<script lang="ts">
	import type { NobelRow, Metric } from '$nobel/data';

	let { rows, metrics }: { rows: NobelRow[]; metrics: Metric[] } = $props();

	// Client-side sorting. The reader clicks a column header to sort by it; a
	// column key identifies which value to compare. Identity columns read a field
	// straight off the row; rank columns (the metric keys) read from `row.ranks`.
	// Clicking cycles through: ascending → descending → back to the dataset's
	// natural order. `null`/blank values always sort to the bottom regardless of
	// direction, so an active sort never buries the sparse rows out of reach.
	type SortDir = 'asc' | 'desc';
	let sortKey = $state<string | null>(null);
	let sortDir = $state<SortDir>('asc');

	// Identity columns whose value lives directly on the row. Anything not here is
	// treated as a rank metric key and read from `row.ranks`.
	const identityKeys = new Set([
		'name',
		'category',
		'year',
		'country',
		'gender',
		'awardAge',
		'fatherOcc',
		'foundOcc'
	]);

	function sortValue(row: NobelRow, key: string): string | number | null {
		if (identityKeys.has(key)) {
			return (row as unknown as Record<string, string | number | null>)[key];
		}
		return row.ranks[key] ?? null;
	}

	function sortBy(key: string): void {
		if (sortKey !== key) {
			sortKey = key;
			sortDir = 'asc';
		} else if (sortDir === 'asc') {
			sortDir = 'desc';
		} else {
			// Third click on the same column clears the sort.
			sortKey = null;
			sortDir = 'asc';
		}
		page = 1;
	}

	/** aria-sort value for a header, so assistive tech announces the sort state. */
	function ariaSort(key: string): 'ascending' | 'descending' | 'none' {
		if (sortKey !== key) return 'none';
		return sortDir === 'asc' ? 'ascending' : 'descending';
	}

	let search = $state('');
	const visibleMetrics = $derived(metrics.filter((metric) => metric.key !== 'prestige_rank'));

	// Search the displayed values, including the prize and year beside each name.
	const filteredRows = $derived.by(() => {
		const query = search.trim().toLocaleLowerCase();
		if (!query) return rows;
		return rows.filter((row) => [
			`${row.name} (${row.category} ${row.year})`,
			row.country,
			titleCase(row.gender),
			fmtNum(row.awardAge),
			row.fatherOcc || '—',
			row.foundOcc || '—',
			...visibleMetrics.map((metric) => fmtRank(row.ranks[metric.key] ?? null))
		].some((value) => value.toLocaleLowerCase().includes(query)));
	});

	const sortedRows = $derived.by(() => {
		if (sortKey == null) return filteredRows;
		const key = sortKey;
		const dir = sortDir === 'asc' ? 1 : -1;
		// Copy before sorting so the source `rows` prop is never mutated.
		return [...filteredRows].sort((a, b) => {
			const av = sortValue(a, key);
			const bv = sortValue(b, key);
			const aEmpty = av == null || av === '';
			const bEmpty = bv == null || bv === '';
			if (aEmpty && bEmpty) return 0;
			if (aEmpty) return 1; // empties always last
			if (bEmpty) return -1;
			let cmp: number;
			if (typeof av === 'number' && typeof bv === 'number') {
				cmp = av - bv;
			} else {
				cmp = String(av).localeCompare(String(bv));
			}
			return cmp * dir;
		});
	});

	// Client-side pagination. 1-indexed page; page size is reader-selectable.
	const pageSizes = [2, 5, 25, 50];
	let pageSize = $state(5);
	let page = $state(1);

	const total = $derived(sortedRows.length);
	const totalPages = $derived(Math.max(1, Math.ceil(total / pageSize)));
	const start = $derived((page - 1) * pageSize);
	const pagedRows = $derived(sortedRows.slice(start, start + pageSize));
	// Human-readable "showing X–Y of Z" range (1-indexed, inclusive).
	const rangeStart = $derived(total === 0 ? 0 : start + 1);
	const rangeEnd = $derived(Math.min(start + pageSize, total));

	// Keep the page in range if the row list shrinks (e.g. filtering) or the
	// page size grows past the current page.
	$effect(() => {
		if (page > totalPages) page = totalPages;
	});

	function goTo(p: number): void {
		page = Math.min(Math.max(1, p), totalPages);
	}
	function changePageSize(e: Event): void {
		pageSize = Number((e.currentTarget as HTMLSelectElement).value);
		page = 1;
	}

	// Compact header labels for the rank metrics (the dataset's own `label` is
	// tuned for a chart dropdown and is too long for a table header). Keyed by
	// metric key; falls back to the metric label if a key is ever unmapped.
	const rankShortLabels: Record<string, string> = {
		med_inctot_rank: "Father income (national)",
		global_med_inctot_rank: "Father income (global)",
		educ_rank: 'Father education'
	};

	/** Percentile ranks are 0–100; one decimal is plenty. Null → em dash. */
	function fmtRank(v: number | null): string {
		return v == null ? '—' : v.toFixed(1);
	}

	function fmtNum(v: number | null): string {
		return v == null ? '—' : String(v);
	}

	function titleCase(s: string): string {
		return s ? s[0].toUpperCase() + s.slice(1) : s;
	}

	// Identity column headers, in display order. Rank columns come from `metrics`.
	// The two father occupation columns sit together so the reader can
	// compare the paper's coded value against what the grounded search surfaced.
	const identityColumns = [
		{ key: 'name', label: 'Laureate', cls: 'col-name' },
		{ key: 'country', label: 'Country', cls: '' },
		{ key: 'gender', label: 'Gender', cls: '' },
		{ key: 'awardAge', label: 'Award age', cls: 'num' },
		{ key: 'fatherOcc', label: 'Father Occupation', cls: 'col-occ' },
		{ key: 'foundOcc', label: 'Father Occupation (Gemini)', cls: 'col-occ' }
	];

	// Expandable per-row provenance. Each laureate's row can reveal a detail
	// panel with the grounded search's supporting quote, its reasoning, and the
	// source URLs it consulted — progressive disclosure keeps the grid legible
	// while making the "where did this come from?" trail one click away. Tracked
	// by stable `row.id` so an open row survives sorting and pagination; a fresh
	// Set on each toggle keeps Svelte's reactivity honest.
	let expanded = $state<Set<number>>(new Set());

	function isOpen(id: number): boolean {
		return expanded.has(id);
	}
	function toggleRow(id: number): void {
		const next = new Set(expanded);
		if (next.has(id)) next.delete(id);
		else next.add(id);
		expanded = next;
	}
	/** Only rows carrying at least one grounded-search field are expandable. */
	function hasProvenance(row: NobelRow): boolean {
		return !!(row.foundOcc || row.evidenceQuote || row.occReasoning || row.sources.length);
	}
	/** Short, human-readable label for a source link (bare hostname). */
	function sourceLabel(url: string): string {
		try {
			return new URL(url).hostname.replace(/^www\./, '');
		} catch {
			return url;
		}
	}

	// The detail row spans every column: the leading expander, all identity
	// columns, and every rank column. Derived so it tracks a changing metric set.
	const colSpan = $derived(1 + identityColumns.length + visibleMetrics.length);
</script>

<!--
	A sortable column header: a full-cell button that toggles the sort on click,
	with an arrow marking the active direction. `aria-sort` on the <th> lets
	assistive tech announce the state.
-->
{#snippet sortableTh(key: string, label: string, cls: string, titleAttr: string | undefined)}
	<th scope="col" class="{cls} sortable" title={titleAttr} aria-sort={ariaSort(key)}>
		<button
			type="button"
			class="sort-btn"
			class:active={sortKey === key}
			onclick={() => sortBy(key)}
		>
			<span class="sort-label">{label}</span>
			<span class="sort-ind" aria-hidden="true">
				{#if sortKey === key}{sortDir === 'asc' ? '▲' : '▼'}{/if}
			</span>
		</button>
	</th>
{/snippet}

<div class="search ui">
	<input
		type="search"
		aria-label="Search all columns"
		placeholder="Filter by name, occupation, country…"
		bind:value={search}
		oninput={() => { page = 1; }}
	/>
</div>

<div class="table-wrap">
	<table class="ui data-table">
		<thead>
			<tr>
				<th scope="col" class="col-expand">Sources</th>
				{#each identityColumns as col (col.key)}
					{@render sortableTh(col.key, col.label, col.cls, undefined)}
				{/each}
				{#each visibleMetrics as m (m.key)}
					{@render sortableTh(m.key, rankShortLabels[m.key] ?? m.label, 'num rank', m.axisLabel)}
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each pagedRows as row (row.id)}
				<tr class:has-detail={isOpen(row.id)}>
					<td class="col-expand">
						{#if hasProvenance(row)}
							<button
								type="button"
								class="expand-btn"
								class:open={isOpen(row.id)}
								aria-expanded={isOpen(row.id)}
								aria-label={isOpen(row.id)
									? `Hide sources for ${row.name}`
									: `Show sources for ${row.name}`}
								onclick={() => toggleRow(row.id)}
							>
								<span class="chev" aria-hidden="true">▸</span>
								<span class="expand-text">{isOpen(row.id) ? 'Hide' : 'Show'}</span>
							</button>
						{/if}
					</td>
					<th scope="row" class="col-name">
						<strong>{row.name}</strong> ({row.category} {row.year})
					</th>
					<td>{row.country}</td>
					<td>{titleCase(row.gender)}</td>
					<td class="num">{fmtNum(row.awardAge)}</td>
					<td class="col-occ">{row.fatherOcc || '—'}</td>
					<td class="col-occ">{row.foundOcc || '—'}</td>
					{#each visibleMetrics as m (m.key)}
						<td class="num rank">{fmtRank(row.ranks[m.key] ?? null)}</td>
					{/each}
				</tr>
				{#if isOpen(row.id)}
					<tr class="detail-row">
						<td colspan={colSpan}>
							<div class="detail">
								<p class="detail-caption ui">
									Results from a Gemini grounded web search for
									<strong>{row.name}</strong>'s father.
								</p>
								{#if row.sources.length}
									<div class="detail-block">
										<span class="detail-label ui">Sources ({row.sources.length})</span>
										<ul class="detail-sources ui">
											{#each row.sources as url (url)}
												<li>
													<a href={url} target="_blank" rel="noopener noreferrer" title={url}>
														{sourceLabel(url)}
													</a>
												</li>
											{/each}
										</ul>
									</div>
								{/if}
								{#if row.occReasoning}
									<div class="detail-block">
										<span class="detail-label ui">Occupation reasoning</span>
										<p class="detail-text">{row.occReasoning}</p>
									</div>
								{/if}
								{#if row.evidenceQuote}
									<div class="detail-block">
										<span class="detail-label ui">Evidence quote</span>
										<blockquote class="detail-quote">{row.evidenceQuote}</blockquote>
									</div>
								{/if}
							</div>
						</td>
					</tr>
				{/if}
			{:else}
				<tr><td colspan={colSpan}>No laureates match your search.</td></tr>
			{/each}
		</tbody>
	</table>
</div>

<nav class="pager ui" aria-label="Table pagination">
	<span class="range">
		{rangeStart.toLocaleString()}–{rangeEnd.toLocaleString()} of {total.toLocaleString()}
	</span>

	<label class="page-size">
		Rows
		<select value={pageSize} onchange={changePageSize}>
			{#each pageSizes as size (size)}
				<option value={size}>{size}</option>
			{/each}
		</select>
	</label>

	<div class="pager-controls">
		<button type="button" onclick={() => goTo(1)} disabled={page <= 1} aria-label="First page">
			«
		</button>
		<button type="button" onclick={() => goTo(page - 1)} disabled={page <= 1} aria-label="Previous page">
			‹
		</button>
		<span class="page-of">Page {page} of {totalPages}</span>
		<button
			type="button"
			onclick={() => goTo(page + 1)}
			disabled={page >= totalPages}
			aria-label="Next page"
		>
			›
		</button>
		<button
			type="button"
			onclick={() => goTo(totalPages)}
			disabled={page >= totalPages}
			aria-label="Last page"
		>
			»
		</button>
	</div>
</nav>

<style>
	.search {
		display: grid;
		gap: 0.4rem;
		max-width: 28rem;
		margin-bottom: 1rem;
		font-size: 0.85rem;
		color: var(--muted);
	}
	.search input {
		width: 100%;
		box-sizing: border-box;
		font: inherit;
		color: var(--ink);
		background: var(--bg);
		border: 1px solid var(--rule-strong);
		border-radius: 5px;
		padding: 0.5rem 0.65rem;
	}
	.search input:focus-visible {
		outline: 2px solid var(--accent);
		outline-offset: 2px;
	}

	/* The table scrolls independently on both axes inside this container so wide
	   content never forces the page body to scroll horizontally, and the long row
	   list stays contained. The sticky header rides the vertical scroll. */
	.table-wrap {
		overflow: auto;
		max-height: 54vh;
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
		font-weight: 700;
		font-size: 0.72rem;
		letter-spacing: 0.02em;
		color: var(--ink);
		white-space: nowrap;
		padding: 0.6rem 0.75rem;
		border-bottom: 1px solid var(--rule-strong);
	}

	/* Sortable headers move their padding onto the inner button so the whole cell
	   is the click target. The button is a bare, full-width control that inherits
	   the header type; an arrow marks the active sort direction. */
	thead th.sortable {
		padding: 0;
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
	.sort-btn:hover {
		color: var(--accent);
	}
	.sort-btn.active {
		color: var(--accent);
	}
	.sort-btn:focus-visible {
		outline: 2px solid var(--accent);
		outline-offset: -2px;
	}
	/* Reserve space for the arrow so activating a sort doesn't shift the label. */
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
		/* Row headers (the Laureate cell) are <th>, which browsers centre by
		   default — align them with the rest of the text columns. */
		text-align: left;
	}

	/* Zebra striping for scan-ability across many columns. */
	tbody tr:nth-child(even) th,
	tbody tr:nth-child(even) td {
		background: color-mix(in srgb, var(--bg-panel) 55%, transparent);
	}
	tbody tr:hover th,
	tbody tr:hover td {
		background: color-mix(in srgb, var(--accent) 7%, transparent);
	}

	.col-name {
		color: var(--ink);
		white-space: nowrap;
	}
	tbody th.col-name {
		font-weight: 400;
	}
	.col-occ {
		min-width: 12rem;
		color: var(--muted);
	}

	/* Leading disclosure column: holds a clearly-clickable "Show/Hide" pill. */
	.col-expand {
		width: 1%;
		white-space: nowrap;
	}
	thead th.col-expand {
		font-size: 0.72rem;
	}
	/* A small pill button so the affordance reads as clickable at a glance —
	   bordered, tinted, with a chevron + label (not a bare glyph). */
	.expand-btn {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0.2rem 0.5rem;
		font: inherit;
		font-size: 0.72rem;
		font-weight: 600;
		line-height: 1;
		color: var(--accent);
		background: color-mix(in srgb, var(--accent) 8%, transparent);
		border: 1px solid color-mix(in srgb, var(--accent) 35%, transparent);
		border-radius: 999px;
		cursor: pointer;
	}
	.expand-btn:hover {
		background: color-mix(in srgb, var(--accent) 16%, transparent);
		border-color: var(--accent);
	}
	.expand-btn:focus-visible {
		outline: 2px solid var(--accent);
		outline-offset: 1px;
	}
	.chev {
		font-size: 0.62rem;
		line-height: 1;
		transition: transform 0.12s ease;
	}
	.expand-btn.open .chev {
		transform: rotate(90deg);
	}
	.expand-text {
		letter-spacing: 0.01em;
	}

	/* Parent of an open detail row: subtle tint ties the pair together and the
	   bottom border is dropped so the row reads as continuous with its panel. */
	tbody tr.has-detail th,
	tbody tr.has-detail td {
		background: color-mix(in srgb, var(--accent) 6%, transparent);
		border-bottom-color: transparent;
	}

	/* The expanded provenance panel. Spans all columns; its own background sets
	   it off from the striped data rows regardless of their odd/even position. */
	.detail-row > td {
		padding: 0;
		background: color-mix(in srgb, var(--accent) 6%, transparent);
	}
	.detail {
		max-width: var(--read-max);
		padding: 0.4rem 1rem 1rem 2.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.85rem;
	}
	.detail-caption {
		margin: 0;
		font-size: 0.75rem;
		color: var(--muted);
	}
	.detail-caption strong {
		color: var(--ink-soft);
		font-weight: 600;
	}
	.detail-block {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}
	.detail-label {
		font-size: 0.68rem;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--accent);
	}
	.detail-quote {
		margin: 0;
		padding: 0.1rem 0 0.1rem 0.85rem;
		border-left: 2px solid var(--rule-strong);
		font-family: var(--font-serif);
		font-style: italic;
		font-size: 0.9rem;
		line-height: 1.5;
		color: var(--ink);
	}
	.detail-text {
		margin: 0;
		font-size: 0.85rem;
		line-height: 1.55;
		color: var(--ink-soft);
	}
	.detail-sources {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem 0.9rem;
		margin: 0;
		padding: 0;
		list-style: none;
		font-size: 0.8rem;
	}
	.detail-sources a {
		color: var(--accent);
		text-decoration: none;
		word-break: break-word;
	}
	.detail-sources a:hover {
		text-decoration: underline;
	}

	.num {
		text-align: right;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	th.num {
		text-align: right;
	}
	/* Rank columns read as a related block, set off from the identity columns. */
	.rank {
		color: var(--ink-soft);
	}
	thead th.rank {
		max-width: 6.5rem;
		white-space: normal;
	}

	/* Pagination bar under the table. Range on the left, page-size in the middle,
	   prev/next controls on the right; wraps to a stack on narrow viewports. */
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
