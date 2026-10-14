<!--
	FigureMostCommonOccup — appendix figure: the most common father occupations
	among Nobel laureates, compared with the general population.

	Why this file exists:
	    Surfaces `most_common_occupations.json` (top-10 father occupations) as a
	    compact horizontal bar chart in the right-hand pane: for each occupation,
	    the laureate share and the census (population) share side by side, sorted
	    by laureate share. The gap between the two bars is the over-representation
	    the prose refers to.

	    Built with @devdatalab/ddl-charts container/scale primitives and D3.

	Upstream dependencies:
	    $nobel/data (mostCommonOccupationsData from most_common_occupations.json)
	    @devdatalab/ddl-charts, d3
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';
	import { createChartContainer, createContainer, createLinearScale } from '@devdatalab/ddl-charts';
	import { mostCommonOccupationsData } from '$nobel/data';
	import { replicationSourceUrl } from '$lib/reading/replicationSource';
	import { resolveCanvasFont, maxLabelWidth, fitLabel } from '$lib/charts/labelFit';
	import { BARE_CLASS, useBareChrome } from '$lib/reading/brandChrome';

	// Bare (no DDL wrapper) in the Additional Information pane, which is the only
	// place this figure is rendered.
	const bare = useBareChrome();

	let { caption }: { caption?: string | null } = $props();

	const LAUREATE = '#1e88e5';
	const CENSUS = '#b0bec5';

	// Top-10 occupations, most common among laureate fathers first.
	const rows = [...mostCommonOccupationsData.data.top10]
		.sort((a, b) => b.nobelists_pct - a.nobelists_pct)
		.slice(0, 10);

	let host: HTMLDivElement;
	let redraw: () => void = () => {};

	onMount(() => {
		// The occupation labels sit in the left gutter, right-anchored `labelGap`px
		// from the plot. Measure their real pixel widths (pretext, via the font the
		// labels actually inherit) and size the gutter to the widest — clamped so a
		// single long label can't swallow the plot on a narrow right-pane. Replaces
		// the old fixed `left: 128` magic number and character-count truncation.
		const LABEL_PX = 11;
		const labelGap = 8;
		const labelFont = resolveCanvasFont(host, LABEL_PX);
		const labelsMax = maxLabelWidth(rows.map((r) => r.label), labelFont);
		const gutter = Math.min(168, Math.max(72, Math.ceil(labelsMax) + labelGap + 4));
		// Pixels available to a label before it reaches the plot's left edge.
		const labelMaxPx = gutter - labelGap - 2;

		const margin = { top: 8, right: 44, bottom: 34, left: gutter };
		const rowH = 26;
		const height = margin.top + margin.bottom + rows.length * rowH;

		const cc = createChartContainer(host, {
			title: caption ?? undefined,
			source: 'most_common_occupations/most_common_occupations.py',
			sourceUrl:
				replicationSourceUrl('most_common_occupations/most_common_occupations.py'),
			showBranding: !bare,
			className: bare ? BARE_CLASS : ''
		});

		const { container, chartArea, dimensions } = createContainer(d3.select(cc.body), {
			height,
			margin,
			responsive: true,
			onResize: () => redraw()
		});

		function render() {
			const { innerWidth, innerHeight } = dimensions;
			chartArea.selectAll('*').remove();

			const xMax = Math.max(...rows.map((r) => Math.max(r.nobelists_pct, r.census_pct)));
			const xScale = createLinearScale({ domain: [0, xMax * 1.08], range: [0, innerWidth] });
			const band = innerHeight / rows.length;
			const barH = Math.min(8, (band - 6) / 2);

			// X gridlines + axis
			const ticks = xScale.ticks(4);
			chartArea
				.append('g')
				.selectAll('line')
				.data(ticks)
				.join('line')
				.attr('x1', (t: number) => xScale(t))
				.attr('x2', (t: number) => xScale(t))
				.attr('y1', 0)
				.attr('y2', innerHeight)
				.attr('stroke', 'var(--rule, #e7e7e4)')
				.attr('stroke-width', 1);
			chartArea
				.append('g')
				.selectAll('text')
				.data(ticks)
				.join('text')
				.attr('x', (t: number) => xScale(t))
				.attr('y', innerHeight + 16)
				.attr('text-anchor', 'middle')
				.attr('font-size', '10px')
				.attr('fill', 'var(--muted, #888)')
				.text((t: number) => `${t}%`);
			chartArea
				.append('text')
				.attr('x', innerWidth / 2)
				.attr('y', innerHeight + 30)
				.attr('text-anchor', 'middle')
				.attr('font-size', '10px')
				.attr('fill', 'var(--muted, #888)')
				.text('Share of fathers (%)');

			rows.forEach((r, i) => {
				const yc = i * band + band / 2;
				const g = chartArea.append('g');

				// Occupation label
				g.append('text')
					.attr('x', -labelGap)
					.attr('y', yc)
					.attr('text-anchor', 'end')
					.attr('dominant-baseline', 'middle')
					.attr('font-size', `${LABEL_PX}px`)
					.attr('fill', 'var(--ink, #1a1a1a)')
					.text(fitLabel(r.label, labelMaxPx, labelFont))
					.append('title')
					.text(`${r.label} — ${r.occ_share_ratio.toFixed(1)}× over-represented`);

				// Laureate bar (top) + census bar (bottom)
				g.append('rect')
					.attr('x', 0)
					.attr('y', yc - barH - 1)
					.attr('width', Math.max(xScale(r.nobelists_pct), 0))
					.attr('height', barH)
					.attr('fill', LAUREATE);
				g.append('rect')
					.attr('x', 0)
					.attr('y', yc + 1)
					.attr('width', Math.max(xScale(r.census_pct), 0))
					.attr('height', barH)
					.attr('fill', CENSUS);

				// Over-representation ratio at bar end
				g.append('text')
					.attr('x', xScale(r.nobelists_pct) + 4)
					.attr('y', yc - 1)
					.attr('dominant-baseline', 'middle')
					.attr('font-size', '9.5px')
					.attr('fill', 'var(--muted, #888)')
					.text(`${r.occ_share_ratio.toFixed(1)}×`);
			});
		}

		redraw = render;
		render();

		// Legend
		const legend = document.createElement('p');
		legend.className = 'ddl-chart-note';
		legend.innerHTML =
			'<span style="color:#1e88e5">▮</span> Laureate fathers &nbsp; <span style="color:#90a4ae">▮</span> U.S. working population, averaged across 1850–1970.';
		cc.container.insertBefore(legend, cc.footer);

		return () => {
			container.dispatch('remove');
			host.replaceChildren();
		};
	});
</script>

<figure class="viz-figure">
	<div class="chart-host" bind:this={host}></div>
</figure>

<style>
	.viz-figure {
		margin: 0;
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
