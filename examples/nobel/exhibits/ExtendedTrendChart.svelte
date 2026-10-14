<!--
	ExtendedTrendChart — one prize-year binscatter panel for the Extended Results
	explorer (/extended-results).

	Why this file exists:
		The explorer shows three trend panels (average rank, share in top 10%,
		share in top 20%) that must re-render whenever the reader switches SES
		measure or subgroup. FigureBinscatterRanks renders a fixed, self-selecting
		set of panels on mount; this component instead takes its points + linear
		fit as reactive props and redraws on change, so the parent can drive four
		charts from one pair of selectors.

		Draws the ddl-charts idiom shared with FigureBinscatterRanks: n-weighted
		blue dots, a dashed red OLS fit line between the 1901/2023 predicted
		endpoints, an in-chart b=…(se)*** slope annotation, and a nearest-point
		tooltip. Fit endpoints are clamped to [0,100] for drawing only (thin
		samples can predict out of range); the annotation reports the true slope.

	Upstream dependencies:
		$nobel/data (ExtendedTrendPoint, ExtendedFit types)
		@devdatalab/ddl-charts, d3
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';
	import {
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
	import type { ExtendedTrendPoint, ExtendedFit } from '$nobel/data';

	let {
		points,
		fit,
		yLabel,
		asPercent = false
	}: {
		points: ExtendedTrendPoint[];
		fit: ExtendedFit;
		yLabel: string;
		asPercent?: boolean;
	} = $props();

	let host: HTMLDivElement;
	let ready = $state(false);
	// ddl-charts container handles, created once on mount, read by render().
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	let container: any, svg: any, chartArea: any, dimensions: any;
	let redraw: () => void = () => {};
	let hitPoints: { id: number; x: number; y: number }[] = [];

	const clamp = (v: number) => Math.max(0, Math.min(100, v));

	function slopeLabel(f: ExtendedFit): string {
		if (f.coef == null || f.se == null) return '';
		// Match the reference's b=…(se)*** convention (leading zero dropped).
		const b = f.coef.toFixed(2).replace(/^(-?)0\./, '$1.');
		const se = Math.abs(f.se).toFixed(2);
		const stars = f.p == null ? '' : f.p < 0.01 ? '***' : f.p < 0.05 ? '**' : f.p < 0.1 ? '*' : '';
		return `b=${b} (${se})${stars}`;
	}

	onMount(() => {
		// bottom leaves room for the x-axis label (createXAxis draws it 50px below
		// the axis line); left keeps the rotated y-label clear of the tick labels.
		const margin = { top: 16, right: 70, bottom: 56, left: 56 };
		const built = createContainer(d3.select(host), {
			height: 260,
			margin,
			responsive: true,
			onResize: () => redraw()
		});
		container = built.container;
		svg = built.svg;
		chartArea = built.chartArea;
		dimensions = built.dimensions;
		createTooltip(container);
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

	// Redraw whenever the active cell's data changes (measure / subgroup switch).
	$effect(() => {
		points;
		fit;
		if (ready) redraw();
	});

	function render() {
		const { innerWidth, innerHeight } = dimensions;
		chartArea.selectAll('*').remove();

		const xScale = createLinearScale({ domain: [1900, 2025], range: [0, innerWidth] });
		const yScale = createLinearScale({ domain: [0, 100], range: [innerHeight, 0] });

		createYAxis(chartArea, yScale, {
			x: 0,
			grid: true,
			gridWidth: innerWidth,
			tickCount: 5,
			labelX: -44,
			label: yLabel
		});
		createXAxis(chartArea, xScale, {
			y: innerHeight,
			tickFormat: d3.format('d'),
			tickCount: 6,
			label: 'Prize year'
		});

		// Dashed OLS fit line + endpoint markers.
		if (fit.coef != null && fit.predStart.y != null && fit.predEnd.y != null) {
			chartArea
				.append('line')
				.attr('x1', xScale(fit.predStart.x))
				.attr('y1', yScale(clamp(fit.predStart.y)))
				.attr('x2', xScale(fit.predEnd.x))
				.attr('y2', yScale(clamp(fit.predEnd.y)))
				.attr('stroke', '#d62728')
				.attr('stroke-width', 1.5)
				.attr('stroke-dasharray', '6,3');
			for (const e of [fit.predStart, fit.predEnd]) {
				if (e.y == null) continue;
				chartArea
					.append('circle')
					.attr('cx', xScale(e.x))
					.attr('cy', yScale(clamp(e.y)))
					.attr('r', 3)
					.attr('fill', '#d62728');
			}
			chartArea
				.append('text')
				.attr('x', innerWidth - 2)
				.attr('y', 11)
				.attr('text-anchor', 'end')
				.attr('font-size', '11px')
				.attr('fill', '#d62728')
				.text(slopeLabel(fit));
		}

		// Binscatter dots, radius growing with n (matches the reference plot).
		const pts = points.map((p, i) => ({
			id: i,
			x: xScale(p.x),
			y: yScale(clamp(p.y)),
			d: p
		}));
		type Pt = (typeof pts)[0];
		chartArea
			.append('g')
			.selectAll('circle')
			.data(pts)
			.join('circle')
			.attr('cx', (d: Pt) => d.x)
			.attr('cy', (d: Pt) => d.y)
			.attr('r', (d: Pt) => 3 + Math.min(3.2, Math.sqrt(d.d.n) * 0.45))
			.attr('fill', '#1e88e5')
			.attr('stroke', 'white')
			.attr('stroke-width', 1);

		hitPoints = pts.map((p) => ({ id: p.id, x: p.x, y: p.y }));
		const byId = new Map(pts.map((p) => [p.id, p]));

		svg
			.on('mousemove', function (event: MouseEvent) {
				const [mx, my] = d3.pointer(event, chartArea.node());
				const hitId = nearestPoint(hitPoints, mx, my, 20);
				if (hitId == null) {
					hideTooltip(container);
					return;
				}
				const pt = byId.get(hitId as number);
				if (!pt) return;
				const val = asPercent ? `${pt.d.y.toFixed(1)}%` : pt.d.y.toFixed(1);
				showTooltip(
					container,
					`<div style="font-size:12px;">
						<div><strong>${pt.d.binStart}–${pt.d.binEnd}</strong></div>
						<div>${asPercent ? 'Share' : 'Mean rank'}: ${val}</div>
						<div>n = ${pt.d.n}</div>
					</div>`
				);
				const [cx, cy] = d3.pointer(event, container.node());
				positionTooltip(container, cx, cy, { preferAbove: true });
			})
			.on('mouseleave', () => hideTooltip(container));
	}
</script>

<div class="trend-host" bind:this={host} style="min-height:260px"></div>

<style>
	.trend-host {
		width: 100%;
	}
</style>
