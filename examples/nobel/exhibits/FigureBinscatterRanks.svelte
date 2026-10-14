<!--
	FigureBinscatterRanks — Figure 2: "Average Socioeconomic Ranks of Fathers of Nobel Laureates"

	Why this file exists:
	    Renders three binscatter panels (national income rank, education rank,
	    global income rank) showing the average father rank over time, with an
	    OLS regression line. The active panel is selectable via a tab strip.

	    Each panel bins the x-axis variable into fixed 5-year windows and shows the
	    mean father rank within each window (y-axis, plotted at the window
	    midpoint), plus an OLS linear fit estimated on the underlying data.
	    Hovering a dot shows the window's value and rank.

	    The `xAxis` prop selects the horizontal variable: 'prize_year' (default,
	    Figure 2 in the main text) or 'cohort' (father's birth cohort — the
	    appendix "cohort ranks" figure). Both series ship in binscatter_ranks.json.

	    Built with @devdatalab/ddl-charts container/scale/axis primitives and D3.

	Upstream dependencies:
	    $nobel/data (binscatterRanksData from binscatter_ranks.json)
	    @devdatalab/ddl-charts, d3
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import { observeChartWidth } from '$lib/reading/observeChartWidth';
	import * as d3 from 'd3';
	import {
		createChartContainer,
		createContainer,
		createLinearScale,
		createXAxis,
		createYAxis,
		createTooltip,
		showTooltip,
		hideTooltip,
		positionTooltip,
		nearestPoint
	} from '@devdatalab/ddl-charts';
	import { binscatterRanksData } from '$nobel/data';
	import { replicationSourceUrl } from '$lib/reading/replicationSource';
	import { BARE_CLASS, useBareChrome } from '$lib/reading/brandChrome';

	// Branded in the main text; bare in the Additional Information pane.
	const bare = useBareChrome();

	let {
		number,
		caption,
		xAxis = 'prize_year'
	}: {
		number?: string;
		caption?: string | null;
		xAxis?: 'prize_year' | 'cohort';
	} = $props();

	const PANELS = [
		{ key: 'med_inctot_rank', label: 'National income rank' },
		{ key: 'educ_rank', label: 'Education rank' },
		{ key: 'global_med_inctot_rank', label: 'Global income rank' }
	];

	// Per-axis presentation. The cohort series has a wider, older x-range and
	// carries no 1901/2023 anchors, so its trend summary reads off pred_start/end.
	const AXIS = {
		prize_year: { axisLabel: 'Prize year', pointLabel: 'Prize year', binUnit: 'prize years' },
		cohort: { axisLabel: "Father's birth cohort", pointLabel: 'Birth cohort', binUnit: 'birth cohorts' }
	} as const;

	let seriesKey: 'by_prize_year' | 'by_cohort' = $derived(
		xAxis === 'cohort' ? 'by_cohort' : 'by_prize_year'
	);

	let activePanel = $state(PANELS[0].key);
	let host: HTMLDivElement;
	let controlsEl: HTMLDivElement;
	let redraw: () => void = () => {};

	// Trend summary shown next to the tab strip, normalised across both series:
	// prize_year uses the paper's 1901→2023 anchors; cohort uses the fitted
	// endpoints (pred_start → pred_end) since it has no fixed-year anchors.
	let summary = $derived.by(() => {
		const lfit = binscatterRanksData.data[activePanel]?.[seriesKey]?.lfit;
		if (!lfit) return null;
		if (xAxis === 'cohort') {
			return {
				startYear: Math.round(lfit.pred_start.x),
				startRank: lfit.pred_start.y,
				endYear: Math.round(lfit.pred_end.x),
				endRank: lfit.pred_end.y,
				diff: lfit.pred_start.y - lfit.pred_end.y
			};
		}
		return {
			startYear: 1901,
			startRank: lfit.pred_1901 ?? lfit.pred_start.y,
			endYear: 2023,
			endRank: lfit.pred_2023 ?? lfit.pred_end.y,
			diff: lfit.diff_1901_2023 ?? lfit.pred_start.y - lfit.pred_end.y
		};
	});

	onMount(() => {
		const margin = { top: 16, right: 24, bottom: 60, left: 64 };
		const height = 300;

		const cc = createChartContainer(host, {
			title: caption ?? undefined,
			source: 'main_binscatter_ranks/main_binscatter_ranks.py',
			sourceUrl: replicationSourceUrl('main_binscatter_ranks/main_binscatter_ranks.py'),
			showBranding: !bare,
			className: bare ? BARE_CLASS : ''
		});

		// Fold "Figure N" into the title as a small-caps label, and move the
		// panel toggle + regression summary into the header below the title,
		// matching BrandedFrame's label/controls layout for the table components.
		const titleEl = cc.header.querySelector('.ddl-branded-title');
		if (titleEl && number) {
			const labelEl = document.createElement('span');
			labelEl.className = 'ddl-branded-label';
			labelEl.textContent = `Figure ${number}`;
			titleEl.insertBefore(labelEl, titleEl.firstChild);
		}
		if (controlsEl) cc.header.appendChild(controlsEl);

		const { container, svg, chartArea, dimensions } = createContainer(d3.select(cc.body), {
			height,
			margin,
			// Observe the inner content box below, including shell-only resizing.
			responsive: false
		});

		createTooltip(container);
		let hitPoints: { id: number; x: number; y: number }[] = [];

		function render() {
			const { innerWidth, innerHeight } = dimensions;
			chartArea.selectAll('*').remove();

			const entry = binscatterRanksData.data[activePanel];
			const { bins, lfit } = entry[seriesKey];

			// prize_year keeps the fixed [1900, 2025] frame; cohort spans a wider,
			// older range, so derive its domain from the data (padded to decades).
			const xDomain =
				xAxis === 'cohort'
					? ([
							Math.floor(Math.min(...bins.map((b) => b.x)) / 10) * 10,
							Math.ceil(Math.max(...bins.map((b) => b.x)) / 10) * 10
						] as [number, number])
					: ([1900, 2025] as [number, number]);
			// Fixed full 0–100 percentile domain, held constant across panels and
			// across the prize-year / cohort views.
			const yDomain = [0, 100] as [number, number];

			const xScale = createLinearScale({ domain: xDomain, range: [0, innerWidth] });
			const yScale = createLinearScale({ domain: yDomain, range: [innerHeight, 0] });

			createYAxis(chartArea, yScale, {
				x: 0,
				grid: true,
				gridWidth: innerWidth,
				tickCount: 5,
				labelX: -45,
				label: 'Percentile rank (0–100)'
			});
			createXAxis(chartArea, xScale, {
				y: innerHeight,
				tickFormat: d3.format('d'),
				tickCount: Math.max(2, Math.floor(innerWidth / 55)),
				label: AXIS[xAxis].axisLabel
			});

			// Regression line
			chartArea
				.append('line')
				.attr('x1', xScale(lfit.pred_start.x))
				.attr('y1', yScale(lfit.pred_start.y))
				.attr('x2', xScale(lfit.pred_end.x))
				.attr('y2', yScale(lfit.pred_end.y))
				.attr('stroke', '#d62728')
				.attr('stroke-width', 1.5)
				.attr('stroke-dasharray', '6,3');

			// Slope annotation
			const slopeLabel = `${(lfit.coef * 100).toFixed(1)} rank pts / 100 yrs`;
			chartArea
				.append('text')
				.attr('x', innerWidth - 4)
				.attr('y', 12)
				.attr('text-anchor', 'end')
				.attr('font-size', '11px')
				.attr('fill', '#d62728')
				.text(slopeLabel);

			// Scatter dots
			const pts = bins.map((b, i) => ({
				id: i,
				x: xScale(b.x),
				y: yScale(b.y),
				binX: b.x,
				binY: b.y
			}));

			type Pt = (typeof pts)[0];
			chartArea
				.append('g')
				.selectAll('circle')
				.data(pts)
				.join('circle')
				.attr('cx', (d: Pt) => d.x)
				.attr('cy', (d: Pt) => d.y)
				.attr('r', 4)
				.attr('fill', '#1e88e5')
				.attr('stroke', 'white')
				.attr('stroke-width', 1);

			hitPoints = pts.map((p) => ({ id: p.id, x: p.x, y: p.y }));
			const ptById = new Map(pts.map((p) => [p.id, p]));

			svg
				.on('mousemove', function (event: MouseEvent) {
					const [mx, my] = d3.pointer(event, chartArea.node());
					const hitId = nearestPoint(hitPoints, mx, my, 20);
					if (hitId == null) {
						hideTooltip(container);
						return;
					}
					const pt = ptById.get(hitId as number);
					if (!pt) return;
					showTooltip(
						container,
						`<div style="font-size:12px;">
							<div><strong>${AXIS[xAxis].pointLabel}</strong>: ${Math.round(pt.binX)}</div>
							<div><strong>Mean rank</strong>: ${pt.binY.toFixed(1)}</div>
						</div>`
					);
					const [cx, cy] = d3.pointer(event, container.node());
					positionTooltip(container, cx, cy, { preferAbove: true });
				})
				.on('mouseleave', () => hideTooltip(container));
		}

		redraw = render;
		render();
		const stopObserving = observeChartWidth(container.node(), svg, dimensions, render);

		const noteEl = document.createElement('p');
		noteEl.className = 'ddl-chart-note';
		noteEl.textContent =
			`Each dot is the mean father rank within a 5-year window of ${AXIS[xAxis].binUnit}. Dashed red line: OLS linear fit on underlying data.`;
		cc.container.insertBefore(noteEl, cc.footer);

		return () => {
			stopObserving();
			container.dispatch('remove');
			host.replaceChildren();
		};
	});

	function onPanelChange(key: string) {
		activePanel = key;
		redraw();
	}

</script>

<figure class="viz-figure">
	<div class="chart-controls ui" bind:this={controlsEl}>
		<div class="tab-strip" role="tablist" aria-label="Rank measure">
			{#each PANELS as p (p.key)}
				<button
					role="tab"
					aria-selected={activePanel === p.key}
					class:active={activePanel === p.key}
					onclick={() => onPanelChange(p.key)}
				>{p.label}</button>
			{/each}
		</div>
		{#if summary}
			<span class="lfit-summary">
				{summary.startRank.toFixed(0)}th pctile in {summary.startYear} → {summary.endRank.toFixed(0)}th in {summary.endYear}
				(−{summary.diff.toFixed(1)} pts)
			</span>
		{/if}
	</div>

	<div class="chart-host" bind:this={host} style="min-height:320px"></div>
</figure>

<style>
	.viz-figure {
		margin: 2rem 0;
	}

	.chart-controls {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.5rem 1rem;
		margin-top: 0.6rem;
	}

	.tab-strip {
		display: flex;
		gap: 0.25rem;
		flex-wrap: wrap;
	}

	.tab-strip button {
		font-family: var(--font-ui);
		font-size: 0.8rem;
		padding: 0.3rem 0.65rem;
		border: 1px solid var(--rule-strong);
		border-radius: 3px;
		background: var(--bg);
		color: var(--ink-soft);
		cursor: pointer;
		transition: background 0.1s, color 0.1s;
	}

	.tab-strip button.active {
		background: var(--accent);
		color: #fff;
		border-color: var(--accent);
	}

	.lfit-summary {
		font-size: 0.8rem;
		color: var(--muted);
		font-variant-numeric: tabular-nums;
	}

	.chart-host {
		width: 100%;
	}

	.chart-host :global(.ddl-branded-header) {
		padding-top: 0;
		padding-bottom: 8px;
	}
	/* Frame-only spacing: these margins exist to clear the wrapper's top edge and
	   inner gutter. Bare, in the Additional Information pane, there is no edge to
	   clear — app.css lines everything up flush instead, so these must not apply. */
	.chart-host :global(.ddl-branded-container:not(.ddl-bare) .ddl-branded-title) {
		margin-top: 16.2px;
	}
	.chart-host :global(.ddl-branded-label) {
		display: inline-block;
		font-size: 0.72em;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--accent);
		margin-right: 0.5em;
	}
	.chart-host :global(.ddl-branded-container:not(.ddl-bare) .ddl-branded-body) {
		padding-left: 32px;
		padding-right: 0;
		padding-top: 4px;
		padding-bottom: 0;
	}
	.chart-host :global(.ddl-chart-note) {
		margin: 0;
		font-size: 0.78rem;
		color: var(--muted, #888);
		line-height: 1.5;
		font-family: var(--font-ui);
	}
	.chart-host :global(.ddl-branded-container:not(.ddl-bare) .ddl-chart-note) {
		padding: 2px 24px 6px;
	}
</style>
