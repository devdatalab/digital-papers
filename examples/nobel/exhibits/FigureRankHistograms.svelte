<!--
	FigureRankHistograms — Figure 1: "Distribution of Socioeconomic Ranks of Fathers of Nobel Laureates"

	Why this file exists:
	    Renders three bar-chart panels (national income rank, education rank,
	    global income rank) showing the distribution of fathers' percentile ranks
	    among Nobel laureates. The panel is selectable via a tab strip. Users can
	    also toggle between the full sample and male/female sub-distributions.

	    Built with @devdatalab/ddl-charts container/scale/axis primitives and D3
	    for the bar rendering, following the NobelRankScatter pattern.

	Upstream dependencies:
	    $nobel/data (rankHistogramsData from rank_histograms.json)
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
		createYAxis
	} from '@devdatalab/ddl-charts';
	import { rankHistogramsData } from '$nobel/data';
	import { replicationSourceUrl } from '$lib/reading/replicationSource';

	let { number, caption }: { number?: string; caption?: string | null } = $props();

	const PANELS = [
		{ key: 'med_inctot_rank', label: 'National income rank' },
		{ key: 'educ_rank', label: 'Education rank' },
		{ key: 'global_med_inctot_rank', label: 'Global income rank' }
	];

	const SERIES = [
		{ key: 'full', label: 'All laureates', color: '#1e88e5' },
		{ key: 'male', label: 'Male', color: '#0072B2' },
		{ key: 'female', label: 'Female', color: '#D55E00' }
	] as const;

	let activePanel = $state(PANELS[0].key);
	let activeSeries = $state<'full' | 'male' | 'female'>('full');

	let host: HTMLDivElement;
	let controlsEl: HTMLDivElement;
	let redraw: () => void = () => {};

	onMount(() => {
		const margin = { top: 16, right: 24, bottom: 60, left: 64 };
		const height = 260;

		const cc = createChartContainer(host, {
			title: caption ?? undefined,
			source: 'rank_histograms/rank_histograms.py',
			sourceUrl: replicationSourceUrl('rank_histograms/rank_histograms.py')
		});

		// Fold "Figure N" into the title as a small-caps label, and move the
		// panel/series toggle controls into the header below the title,
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

		function render() {
			const { innerWidth, innerHeight } = dimensions;
			chartArea.selectAll('*').remove();

			const seriesData = rankHistogramsData.data[activePanel];
			const bins =
				activeSeries === 'full'
					? seriesData.full
					: activeSeries === 'male'
						? seriesData.male
						: seriesData.female;
			if (!bins || bins.length === 0) return;

			const barWidth = innerWidth / bins.length;

			// Fixed 0–100% y-domain so bar heights stay comparable across panels
			// and the male/female/all series toggle.
			const xScale = createLinearScale({ domain: [0, 100], range: [0, innerWidth] });
			const yScale = createLinearScale({ domain: [0, 100], range: [innerHeight, 0] });

			createYAxis(chartArea, yScale, {
				x: 0,
				grid: true,
				gridWidth: innerWidth,
				tickCount: 5,
				labelX: -45,
				label: '% of laureates'
			});
			createXAxis(chartArea, xScale, {
				y: innerHeight,
				tickCount: 5,
				label: 'Father\'s percentile rank'
			});

			const color = SERIES.find((s) => s.key === activeSeries)?.color ?? '#1e88e5';

			type Bin = (typeof bins)[0];
			chartArea
				.append('g')
				.attr('class', 'bars')
				.selectAll('rect')
				.data(bins)
				.join('rect')
				.attr('x', (b: Bin) => xScale(b.x - 2.5) + 1)
				.attr('y', (b: Bin) => yScale(b.pct))
				.attr('width', Math.max(barWidth - 2, 1))
				.attr('height', (b: Bin) => Math.max(innerHeight - yScale(b.pct), 0))
				.attr('fill', color)
				.attr('opacity', 0.8);

		}

		redraw = render;
		render();
		const stopObserving = observeChartWidth(container.node(), svg, dimensions, render);


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

	function onSeriesChange(key: 'full' | 'male' | 'female') {
		activeSeries = key;
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
		<div class="series-strip" role="group" aria-label="Population">
			{#each SERIES as s (s.key)}
				<button
					class:active={activeSeries === s.key}
					onclick={() => onSeriesChange(s.key)}
					style="--dot-color:{s.color}"
				>
					<span class="dot"></span>{s.label}
				</button>
			{/each}
		</div>
	</div>

	<div class="chart-host" bind:this={host} style="min-height:290px"></div>
</figure>

<style>
	.viz-figure {
		margin: 2rem 0;
	}

	.chart-controls {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.5rem 1.5rem;
		margin-top: 0.6rem;
	}

	.tab-strip,
	.series-strip {
		display: flex;
		gap: 0.25rem;
		flex-wrap: wrap;
	}

	.tab-strip button,
	.series-strip button {
		font-family: var(--font-ui);
		font-size: 0.8rem;
		padding: 0.3rem 0.65rem;
		border: 1px solid var(--rule-strong);
		border-radius: 3px;
		background: var(--bg);
		color: var(--ink-soft);
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 0.35rem;
		transition: background 0.1s, color 0.1s;
	}

	.tab-strip button.active,
	.series-strip button.active {
		background: var(--accent);
		color: #fff;
		border-color: var(--accent);
	}

	.series-strip button .dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--dot-color, var(--accent));
		flex: none;
	}

	.series-strip button.active .dot {
		background: #fff;
	}

	.chart-host {
		width: 100%;
	}

	/* padding-left shifts the SVG rightward so the rotated y-axis label (which
	   extends left of the SVG origin) fits within the branded container boundary.
	   margin.right in the chart must be ≥ padding-left to prevent data clipping. */
	.chart-host :global(.ddl-branded-header) {
		padding-top: 0;
		padding-bottom: 8px;
	}
	.chart-host :global(.ddl-branded-title) {
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
	.chart-host :global(.ddl-branded-body) {
		padding-left: 32px;
		padding-right: 0;
		padding-top: 4px;
		padding-bottom: 0;
	}
</style>
