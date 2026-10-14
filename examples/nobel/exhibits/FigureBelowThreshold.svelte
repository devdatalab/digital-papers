<!--
	FigureBelowThreshold — appendix figure: the share of laureates whose fathers
	ranked below the 80th / 90th percentile, over time.

	Why this file exists:
	    Complements the main trend figure by showing the "bottom of the
	    distribution" cut the prose refers to: two sets of binned dots (fathers
	    below the 80th and below the 90th percentile) plotted against prize year,
	    for a selectable rank outcome. Rising shares would mean laureates are
	    increasingly drawn from less-advantaged families.

	    Built with @devdatalab/ddl-charts container/scale/axis primitives and D3.

	Upstream dependencies:
	    $nobel/data (otherRankFunctionsData from other_rank_functions.json)
	    @devdatalab/ddl-charts, d3
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';
	import {
		createChartContainer,
		createContainer,
		createLinearScale,
		createXAxis,
		createYAxis
	} from '@devdatalab/ddl-charts';
	import { otherRankFunctionsData } from '$nobel/data';
	import { replicationSourceUrl } from '$lib/reading/replicationSource';
	import { BARE_CLASS, useBareChrome } from '$lib/reading/brandChrome';

	// Bare (no DDL wrapper) in the Additional Information pane, which is the only
	// place this figure is rendered.
	const bare = useBareChrome();

	let { caption }: { caption?: string | null } = $props();

	const OUTCOMES = [
		{ key: 'med_inctot', label: 'National income' },
		{ key: 'educ', label: 'Education' },
		{ key: 'global_med_inctot', label: 'Global income' }
	];
	const THRESHOLDS = [
		{ key: 'p80', label: 'Below 80th pctile', color: '#e8871e' },
		{ key: 'p90', label: 'Below 90th pctile', color: '#1e88e5' }
	];

	let activeOutcome = $state(OUTCOMES[0].key);
	let host: HTMLDivElement;
	let controlsEl: HTMLDivElement;
	let redraw: () => void = () => {};

	onMount(() => {

		// The x-axis label sits 50px below the plot; reserve space for it inside
		// the SVG so it clears the figure note without shrinking the plot.
		const margin = { top: 16, right: 16, bottom: 64, left: 48 };
		const height = 280;

		const cc = createChartContainer(host, {
			title: caption ?? undefined,
			source: 'other_rank_functions/other_rank_functions.py',
			sourceUrl:
				replicationSourceUrl('other_rank_functions/other_rank_functions.py'),
			showBranding: !bare,
			className: bare ? BARE_CLASS : ''
		});
		if (controlsEl) cc.header.appendChild(controlsEl);

		const { container, chartArea, dimensions } = createContainer(d3.select(cc.body), {
			height,
			margin,
			responsive: true,
			onResize: () => redraw()
		});

		function render() {
			const { innerWidth, innerHeight } = dimensions;
			chartArea.selectAll('*').remove();

			const bt = otherRankFunctionsData.data.below_threshold;
			const series = THRESHOLDS.map((t) => ({
				...t,
				points: bt[t.key]?.[activeOutcome]?.binscatter ?? []
			}));
			const allY = series.flatMap((s) => s.points.map((p) => p.y));
			const yMax = allY.length ? Math.max(...allY) : 0.5;

			const xScale = createLinearScale({ domain: [1900, 2025], range: [0, innerWidth] });
			const yScale = createLinearScale({ domain: [0, Math.max(yMax * 1.15, 0.1)], range: [innerHeight, 0] });

			createYAxis(chartArea, yScale, {
				x: 0,
				grid: true,
				gridWidth: innerWidth,
				tickCount: 5,
				labelX: -38,
				label: 'Share of laureates',
				tickFormat: d3.format('.0%')
			});
			createXAxis(chartArea, xScale, {
				y: innerHeight,
				tickFormat: d3.format('d'),
				tickCount: 6,
				label: 'Prize year'
			});

			for (const s of series) {
				if (!s.points.length) continue;
				chartArea
					.append('g')
					.selectAll('circle')
					.data(s.points)
					.join('circle')
					.attr('cx', (p: { x: number; y: number }) => xScale(p.x))
					.attr('cy', (p: { x: number; y: number }) => yScale(p.y))
					.attr('r', 3)
					.attr('fill', s.color);
			}
		}

		redraw = render;
		render();

		const note = document.createElement('p');
		note.className = 'ddl-chart-note';
		note.textContent =
			'Each dot shows the share of laureates in a given prize-year bin with fathers below the 80th or 90th percentile';
		cc.container.insertBefore(note, cc.footer);

		return () => {
			container.dispatch('remove');
			host.replaceChildren();
		};
	});

	function onOutcomeChange(key: string) {
		activeOutcome = key;
		redraw();
	}
</script>

<figure class="viz-figure">
	<div class="chart-controls ui" bind:this={controlsEl}>
		<div class="tab-strip" role="tablist" aria-label="Rank outcome">
			{#each OUTCOMES as o (o.key)}
				<button
					role="tab"
					aria-selected={activeOutcome === o.key}
					class:active={activeOutcome === o.key}
					onclick={() => onOutcomeChange(o.key)}>{o.label}</button
				>
			{/each}
		</div>
		<div class="legend">
			{#each THRESHOLDS as t (t.key)}
				<span class="legend-item"><span class="swatch" style="background:{t.color}"></span>{t.label}</span>
			{/each}
		</div>
	</div>
	<div class="chart-host" bind:this={host} style="min-height:280px"></div>
</figure>

<style>
	.viz-figure {
		margin: 0;
	}
	.chart-controls {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		margin-top: 0.6rem;
	}
	.tab-strip {
		display: flex;
		gap: 0.25rem;
		flex-wrap: wrap;
	}
	.tab-strip button {
		font-family: var(--font-ui);
		font-size: 0.75rem;
		padding: 0.25rem 0.55rem;
		border: 1px solid var(--rule-strong);
		border-radius: 3px;
		background: var(--bg);
		color: var(--ink-soft);
		cursor: pointer;
	}
	.tab-strip button.active {
		background: var(--accent);
		color: #fff;
		border-color: var(--accent);
	}
	.legend {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
		font-size: 0.74rem;
		color: var(--muted);
	}
	.legend-item {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
	}
	.swatch {
		width: 0.7rem;
		height: 0.7rem;
		border-radius: 2px;
		display: inline-block;
	}
	.chart-host {
		width: 100%;
	}
	/* Body and note padding come from the bare-chrome rules in app.css — this
	   figure only ever renders in the Additional Information pane. */
	.chart-host :global(.ddl-chart-note) {
		margin: 0;
		font-size: 0.74rem;
		color: var(--muted, #888);
		line-height: 1.5;
		font-family: var(--font-ui);
	}
</style>
