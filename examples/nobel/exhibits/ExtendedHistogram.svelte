<!--
	ExtendedHistogram — the father-rank distribution panel for the Extended
	Results explorer (/extended-results).

	Why this file exists:
		The explorer's first panel is a 5-percentile-bin histogram of father ranks
		for the active SES measure × subgroup, and must re-render when either
		selector changes. It mirrors FigureRankHistograms' ddl-charts bar idiom but
		takes its bins as a reactive prop (rather than selecting them from a fixed
		panel set on mount) so the parent can drive it alongside the trend charts.

		The y-domain is scaled to the tallest visible bar (rounded up to a tidy
		multiple) rather than a fixed 0–100, because subgroup share distributions
		concentrate heavily in the top bins and a fixed domain would flatten them.

	Upstream dependencies:
		$nobel/data (ExtendedHistogramBar type)
		@devdatalab/ddl-charts, d3
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';
	import {
		createContainer,
		createLinearScale,
		createXAxis,
		createYAxis
	} from '@devdatalab/ddl-charts';
	import type { ExtendedHistogramBar } from '$nobel/data';

	let { bars }: { bars: ExtendedHistogramBar[] } = $props();

	let host: HTMLDivElement;
	let ready = $state(false);
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	let chartArea: any, dimensions: any, container: any, svg: any;
	let redraw: () => void = () => {};

	onMount(() => {
		// bottom leaves room for the x-axis label (createXAxis draws it 50px below
		// the axis line); left keeps the rotated y-label clear of the tick labels.
		const margin = { top: 16, right: 24, bottom: 56, left: 56 };
		const built = createContainer(d3.select(host), {
			height: 260,
			margin,
			responsive: true,
			onResize: () => redraw()
		});
		container = built.container;
		chartArea = built.chartArea;
		dimensions = built.dimensions;
		svg = built.svg;
		redraw = render;
		ready = true;

		// createContainer only re-measures on window resize, so a client-side
		// navigation that changes the shell width (e.g. arriving from a section
		// page whose right sidebar narrowed the reading column) would leave the
		// SVG sized to the stale, pre-navigation width. Observe the host box
		// directly so the chart re-measures whenever its own width changes.
		const ro = new ResizeObserver(() => {
			const w = host.getBoundingClientRect().width;
			if (!w || w === dimensions.width) return;
			dimensions.width = w;
			dimensions.innerWidth = w - dimensions.margin.left - dimensions.margin.right;
			svg.attr('width', w);
			redraw();
		});
		ro.observe(host);

		return () => {
			ro.disconnect();
			container.dispatch('remove');
			host.replaceChildren();
		};
	});

	$effect(() => {
		bars;
		if (ready) redraw();
	});

	function render() {
		const { innerWidth, innerHeight } = dimensions;
		chartArea.selectAll('*').remove();
		if (!bars.length) return;

		// Round the max share up to a tidy tick so short subgroup samples still
		// read clearly; floor the ceiling at 10% so the axis never collapses.
		const peak = Math.max(...bars.map((b) => b.share));
		const yMax = Math.max(10, Math.ceil(peak / 10) * 10);

		const xScale = createLinearScale({ domain: [0, 100], range: [0, innerWidth] });
		const yScale = createLinearScale({ domain: [0, yMax], range: [innerHeight, 0] });

		createYAxis(chartArea, yScale, {
			x: 0,
			grid: true,
			gridWidth: innerWidth,
			tickCount: 5,
			labelX: -44,
			label: '% of laureates'
		});
		createXAxis(chartArea, xScale, {
			y: innerHeight,
			tickCount: 5,
			label: "Father's percentile rank"
		});

		const barWidth = innerWidth / bars.length;
		type Bar = ExtendedHistogramBar;
		chartArea
			.append('g')
			.selectAll('rect')
			.data(bars)
			.join('rect')
			.attr('x', (b: Bar) => xScale(b.binStart) + 1)
			.attr('y', (b: Bar) => yScale(b.share))
			.attr('width', Math.max(barWidth - 2, 1))
			.attr('height', (b: Bar) => Math.max(innerHeight - yScale(b.share), 0))
			.attr('fill', '#1e88e5')
			.attr('opacity', 0.8)
			.append('title')
			.text((b: Bar) => `${b.binStart}–${b.binEnd}th: ${b.share.toFixed(1)}% (n=${b.n})`);
	}
</script>

<div class="hist-host" bind:this={host} style="min-height:260px"></div>

<style>
	.hist-host {
		width: 100%;
	}
</style>
