<!--
	OccupationRankChart — the Occupation Explorer's primary visualization.

	A two-line time series: for one selected occupation (or occupation group) it
	plots the U.S. national INCOME percentile rank (cranberry, solid, circles) and
	EDUCATION percentile rank (blue, dashed, triangles) of laureate-eligible
	fathers across the census decades 1850–1970. Two selectors drive it: the
	occupation classification level (10 broad groups / 25-group / all occupations)
	and the specific occupation within that level.

	Why compose, not hand-roll: ddl-charts ships no year×rank line primitive, so
	this composes ddl-charts' container/scales/axes/tooltip/legend/nearest-point
	helpers (as NobelRankScatter does) and adds only the line/marker/count-bar D3
	glue. Grouped ranks are raw-U.S.-record-weighted means precomputed upstream;
	this component only draws them.

	`compact` (default false) supports a smaller chart layout: no count bars,
	no right axis, shorter height, and an
	"Open full explorer" link. The full version adds low-opacity U.S.-record count
	bars on a per-selection right axis.

	Upstream dependencies:
	  - $nobel/data (occupationRankTimeseriesData, typed from
	    scripts/site-data/generators/occ_rank_timeseries/)
	  - @devdatalab/ddl-charts (container/scales/axes/tooltip/legend/utils)
	  - d3 (selections, line, axis, pointer, formatting)
	  - $app/paths (base — internal links live under the repo subpath)
	  - $lib/reading/BrandedFrame (DDL-branded chrome: header/controls/footer)
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import * as d3 from 'd3';
	import BrandedFrame from '$lib/reading/BrandedFrame.svelte';
	import {
		createContainer,
		createLinearScale,
		createXAxis,
		createYAxis,
		createTooltip,
		showTooltip,
		hideTooltip,
		positionTooltip,
		createLegend,
		formatNumber
	} from '@devdatalab/ddl-charts';
	import {
		occupationRankTimeseriesData as data,
		type OccupationRankLevelId,
		type OccupationRankOption,
		type OccupationRankPoint
	} from '$nobel/data';

	let { compact = false }: { compact?: boolean } = $props();

	// Classification levels, in the fixed UI order used everywhere.
	const LEVELS: { id: OccupationRankLevelId; short: string }[] = [
		{ id: 'occgroup_10', short: '10 broad groups' },
		{ id: 'occgroup_25', short: '25-group classification' },
		{ id: 'occ1950', short: 'All occupations' }
	];

	// Series colours: cranberry income / primary-blue education. Explicit hex so
	// the two lines stay distinguishable independent of theme tokens; swap for a
	// ddl-charts cranberry token if one is added upstream.
	const INCOME_COLOR = '#A3324C';
	const EDUCATION_COLOR = '#0072B2';
	const COUNT_COLOR = '#9aa0a6';
	const GUIDE_RANK = 80;

	const YEAR_MIN = data.meta.year_min;
	const YEAR_MAX = data.meta.year_max;

	let levelId = $state<OccupationRankLevelId>('occgroup_10');
	let optionId = $state<string>(data.levels.occgroup_10.options[0].id);

	// Options for the current level (already sorted by sort_order upstream).
	const options = $derived<OccupationRankOption[]>(data.levels[levelId].options);
	const selected = $derived(options.find((o) => o.id === optionId) ?? options[0]);
	const rows = $derived<OccupationRankPoint[]>(data.levels[levelId].by_id[optionId]?.rows ?? []);

	// Dropdown label: "<n>. <label> · <k> fathers" for groups, "<code> — <label> ·
	// <k> fathers" for detailed occupations.
	function optionLabel(o: OccupationRankOption): string {
		const lead = levelId === 'occ1950' ? `${o.id} — ${o.label}` : `${o.sort_order}. ${o.label}`;
		return `${lead} · ${o.laureate_n} fathers`;
	}

	// Changing the classification resets to that level's first option (never try to
	// translate a selection across levels).
	function onLevelChange() {
		optionId = data.levels[levelId].options[0].id;
	}

	let host: HTMLDivElement;
	let legendHost: HTMLDivElement;

	// Imperative redraw handle, wired on mount; called by the reactive $effect below.
	let redraw: () => void = () => {};

	onMount(() => {
		// Legend: Income, Education, and (full view only) U.S. records.
		const legendItems = [
			{ id: 'income', label: 'Income rank', color: INCOME_COLOR, visible: true },
			{ id: 'education', label: 'Education rank', color: EDUCATION_COLOR, visible: true }
		];
		if (!compact)
			legendItems.push({ id: 'count', label: 'U.S. records', color: COUNT_COLOR, visible: true });
		createLegend(d3.select(legendHost), legendItems, { position: 'top' });
		// Lay the legend items out in a single row (ddl-legend stacks its item
		// divs vertically by default); wrap only if the container is too narrow.
		d3.select(legendHost)
			.select('.ddl-legend')
			.style('display', 'flex')
			.style('flex-direction', 'row')
			.style('flex-wrap', 'wrap')
			.style('align-items', 'center')
			.style('gap', '0.1rem 0.5rem');

		const height = compact ? 220 : 420;
		// Bottom margin must clear the x-axis ticks *and* the axis label, which
		// ddl-charts places 50px below the axis line (see createXAxis).
		const margin = compact
			? { top: 14, right: 16, bottom: 40, left: 48 }
			: { top: 16, right: 56, bottom: 64, left: 56 };

		const { container, svg, chartArea, dimensions } = createContainer(d3.select(host), {
			height,
			margin,
			responsive: true,
			onResize: () => render()
		});
		createTooltip(container);

		// Redraw on real container-width changes (createContainer only watches
		// window resize; the aside opening/closing changes our width without one).
		const resizeObserver = new ResizeObserver(() => {
			const w = host.getBoundingClientRect().width;
			if (w && w !== dimensions.width) {
				dimensions.width = w;
				dimensions.innerWidth = w - margin.left - margin.right;
				svg.attr('width', w);
				render();
			}
		});
		resizeObserver.observe(host);

		// Per-render hit-testing state (both series' markers).
		type Hit = { series: 'income' | 'education'; x: number; y: number; pt: OccupationRankPoint };
		let hits: Hit[] = [];
		let hoverLayer: d3.Selection<SVGGElement, unknown, null, undefined>;

		function seriesValue(pt: OccupationRankPoint, s: 'income' | 'education'): number | null {
			return s === 'income' ? pt.income_rank : pt.education_rank;
		}

		function render() {
			const iw = dimensions.innerWidth;
			const ih = dimensions.innerHeight;
			chartArea.selectAll('*').remove();
			hits = [];

			const showBars = !compact && iw >= 520;

			const xScale = createLinearScale({ domain: [YEAR_MIN, YEAR_MAX], range: [0, iw], padding: 0.02 });
			const yScale = createLinearScale({ domain: [0, 100], range: [ih, 0] });

			createYAxis(chartArea, yScale, {
				x: 0,
				grid: true,
				gridWidth: iw,
				tickCount: 5,
				// Pull the rotated label inside the left margin so the branded
				// container's overflow:hidden never clips it (default is -60).
				labelX: compact ? -40 : -45,
				label: 'Percentile rank'
			});
			createXAxis(chartArea, xScale, {
				y: ih,
				tickFormat: d3.format('d'),
				tickCount: 7,
				label: 'Census year'
			});

			// Guide line at rank 80.
			chartArea
				.append('line')
				.attr('x1', 0)
				.attr('x2', iw)
				.attr('y1', yScale(GUIDE_RANK))
				.attr('y2', yScale(GUIDE_RANK))
				.attr('stroke', 'var(--rule-strong, #bbb)')
				.attr('stroke-dasharray', '2 3')
				.attr('stroke-width', 1);

			// Count bars behind the lines (full view, wide enough).
			if (showBars) {
				const counts = rows
					.map((r) => r.sample_count)
					.filter((c): c is number => c != null && c > 0);
				const maxCount = counts.length ? Math.max(...counts) : 0;
				if (maxCount > 0) {
					const countScale = d3.scaleLinear().domain([0, maxCount]).range([ih, 0]).nice();
					const bandHalf = Math.max(2, (xScale(YEAR_MIN + 10) - xScale(YEAR_MIN)) * 0.3);
					chartArea
						.append('g')
						.attr('class', 'count-bars')
						.selectAll('rect')
						.data(rows.filter((r) => r.sample_count != null && r.sample_count > 0))
						.join('rect')
						.attr('x', (d: OccupationRankPoint) => xScale(d.year) - bandHalf)
						.attr('width', bandHalf * 2)
						.attr('y', (d: OccupationRankPoint) => countScale(d.sample_count as number))
						.attr('height', (d: OccupationRankPoint) => ih - countScale(d.sample_count as number))
						.attr('fill', COUNT_COLOR)
						.attr('opacity', 0.16);
					// Right axis for the counts.
					const rightAxis = d3.axisRight(countScale).ticks(4).tickFormat(d3.format('~s'));
					chartArea
						.append('g')
						.attr('transform', `translate(${iw},0)`)
						.attr('class', 'count-axis')
						.call(rightAxis)
						.call((g: d3.Selection<SVGGElement, unknown, null, undefined>) =>
							g.select('.domain').remove()
						)
						.append('text')
						.attr('transform', `rotate(90)`)
						.attr('x', ih / 2)
						.attr('y', -44)
						.attr('fill', 'var(--muted, #666)')
						.attr('text-anchor', 'middle')
						.attr('font-size', 11)
						.text('U.S. records');
				}
			}

			// One <g> per series: line (broken on null) + focusable markers.
			for (const s of ['income', 'education'] as const) {
				const color = s === 'income' ? INCOME_COLOR : EDUCATION_COLOR;
				const dash = s === 'income' ? null : '5 4';
				const line = d3
					.line<OccupationRankPoint>()
					.defined((d) => seriesValue(d, s) != null)
					.x((d) => xScale(d.year))
					.y((d) => yScale(seriesValue(d, s) as number));
				const g = chartArea.append('g').attr('class', `series-${s}`);
				g.append('path')
					.datum(rows)
					.attr('fill', 'none')
					.attr('stroke', color)
					.attr('stroke-width', 2.5)
					.attr('stroke-dasharray', dash)
					.attr('d', line);

				const pts = rows.filter((d) => seriesValue(d, s) != null);
				for (const pt of pts) {
					const cx = xScale(pt.year);
					const cy = yScale(seriesValue(pt, s) as number);
					hits.push({ series: s, x: cx, y: cy, pt });
					const marker =
						s === 'income'
							? g.append('circle').attr('cx', cx).attr('cy', cy).attr('r', 4)
							: g
									.append('path')
									.attr('d', d3.symbol().type(d3.symbolTriangle).size(46)())
									.attr('transform', `translate(${cx},${cy})`);
					marker
						.attr('fill', color)
						.attr('stroke', 'white')
						.attr('stroke-width', 1)
						.attr('tabindex', 0)
						.attr('role', 'img')
						.attr(
							'aria-label',
							`${selected.label}, ${s === 'income' ? 'income' : 'education'} rank, ${pt.year}: ` +
								`${formatNumber(seriesValue(pt, s) as number)} percentile` +
								(pt.sample_count == null
									? '; record count unavailable, source rank interpolated'
									: `; ${pt.sample_count.toLocaleString()} U.S. records`)
						)
						.on('focus', () => showHover({ series: s, x: cx, y: cy, pt }, true))
						.on('blur', clearHover);
				}
			}

			hoverLayer = chartArea.append('g').attr('class', 'hover');
		}

		function showHover(
			hit: { series: 'income' | 'education'; x: number; y: number; pt: OccupationRankPoint },
			isFocus = false
		) {
			hoverLayer.selectAll('*').remove();
			const color = hit.series === 'income' ? INCOME_COLOR : EDUCATION_COLOR;
			hoverLayer
				.append('circle')
				.attr('cx', hit.x)
				.attr('cy', hit.y)
				.attr('r', 6.5)
				.attr('fill', 'none')
				.attr('stroke', color)
				.attr('stroke-width', 2)
				.style('pointer-events', 'none');
			const v = seriesValue(hit.pt, hit.series) as number;
			const countLine =
				hit.pt.sample_count == null
					? `<div style="color:var(--muted,#888);">Record count unavailable; source rank is interpolated.</div>`
					: `<div style="color:var(--muted,#888);">${hit.pt.sample_count.toLocaleString()} U.S. records</div>`;
			showTooltip(
				container,
				`<div style="font-weight:600;">${hit.series === 'income' ? 'Income rank' : 'Education rank'} · ${hit.pt.year}</div>` +
					`<div style="font-size:13px;">${formatNumber(v)} percentile</div>` +
					countLine
			);
			if (isFocus) {
				positionTooltip(container, hit.x + margin.left, hit.y + margin.top, { preferAbove: true });
			}
		}
		function clearHover() {
			if (hoverLayer) hoverLayer.selectAll('*').remove();
			hideTooltip(container);
		}

		svg
			.on('mousemove', function (event: MouseEvent) {
				const [mx, my] = d3.pointer(event, chartArea.node());
				let best: Hit | null = null;
				let bestD = 18 * 18;
				for (const h of hits) {
					const d2 = (h.x - mx) ** 2 + (h.y - my) ** 2;
					if (d2 < bestD) {
						bestD = d2;
						best = h;
					}
				}
				if (!best) {
					clearHover();
					return;
				}
				showHover(best);
				const [cx, cy] = d3.pointer(event, container.node());
				positionTooltip(container, cx, cy, { preferAbove: true });
			})
			.on('mouseleave', clearHover);

		redraw = render;
		render();

		return () => {
			resizeObserver.disconnect();
			container.dispatch('remove');
			// `host` lives inside BrandedFrame's `children` snippet, so Svelte's
			// bind:this teardown can null it *before* this cleanup runs (the null
			// timing depends on how much of the tree is torn down together — see
			// svelte/internal .../bindings/this.js). An unguarded call would throw
			// mid-navigation and abort the whole flush (stale TOC, missing aside,
			// unmounted sibling charts). Optional-chain so teardown is null-safe;
			// removing the host element on unmount already drops its D3 children.
			host?.replaceChildren();
		};
	});

	// Redraw whenever the selection changes (after mount wires `redraw`).
	$effect(() => {
		// touch reactive deps so the effect re-runs on change
		void levelId;
		void optionId;
		redraw();
	});
</script>

<!-- The two selectors ride in the branded header's controls slot so they live
     inside the container chrome (not floating above it). -->
{#snippet controls()}
	<div class="occ-controls ui">
		<label class="occ-field">
			<span>Occupation classification</span>
			<select bind:value={levelId} onchange={onLevelChange}>
				{#each LEVELS as lvl (lvl.id)}
					<option value={lvl.id}>{data.levels[lvl.id].label}</option>
				{/each}
			</select>
		</label>
		<label class="occ-field">
			<span>Occupation or group</span>
			<select bind:value={optionId}>
				{#each options as o (o.id)}
					<option value={o.id}>{optionLabel(o)}</option>
				{/each}
			</select>
		</label>
	</div>
{/snippet}

<div class="occ-chart" class:compact>
	<BrandedFrame
		title="Income and education rank over time"
		subtitle="{selected.label} · U.S., {YEAR_MIN}–{YEAR_MAX}"
		source="IPUMS occupation cells (ipums_global_sample.dta). U.S. national percentile ranks; grouped ranks weighted by raw record counts, some cells interpolated."
		{controls}
	>
		<div class="occ-legend" bind:this={legendHost}></div>
		<div class="occ-host" bind:this={host}></div>

		{#if compact}
			<a class="occ-link ui" href="{base}/occupation-rank-explorer">Open full explorer →</a>
		{/if}
	</BrandedFrame>
</div>

<style>
	.occ-chart {
		width: 100%;
		max-width: 100%;
	}
	.occ-controls {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem 1rem;
	}
	.occ-field {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		font-size: 0.78rem;
		color: var(--muted);
	}
	.occ-field > span {
		font-weight: 600;
		letter-spacing: 0.02em;
	}
	.occ-field select {
		font-family: var(--font-ui);
		font-size: 0.82rem;
		color: var(--ink);
		padding: 0.35rem 0.6rem;
		border: 1px solid var(--rule-strong, #ccc);
		border-radius: var(--ddl-border-radius, 4px);
		background: var(--bg, #fff);
		cursor: pointer;
		max-width: min(28rem, 90vw);
	}
	.occ-field select:focus-visible {
		outline: 2px solid var(--accent);
		outline-offset: 1px;
	}
	.occ-legend {
		margin-bottom: 0.4rem;
	}
	.occ-host {
		width: 100%;
	}
	.occ-link {
		display: inline-block;
		margin-top: 0.4rem;
		font-size: 0.8rem;
		color: var(--accent);
		text-decoration: none;
	}
	.occ-link:hover {
		text-decoration: underline;
	}
	.occ-chart :global(.count-axis text),
	.occ-chart :global(.count-axis line) {
		stroke: none;
		color: var(--muted, #888);
	}
</style>
