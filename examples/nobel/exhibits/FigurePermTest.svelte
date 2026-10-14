<!--
	FigurePermTest — Figure 3: "Parent-Child Field Match Randomization Tests"

	Why this file exists:
	    Renders two panels (non-economics sample / economics sample) of the
	    parent-child field match randomization test. Each panel shows a histogram
	    of match shares from 10,000 random simulations (grey bars), with a red
	    vertical line at the empirically observed match share. The p-value is the
	    fraction of simulations achieving at least the observed share.

	    Built with @devdatalab/ddl-charts container/scale/axis primitives and D3.

	Upstream dependencies:
	    $nobel/data (permTestData from parent_field_perm_test.json)
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
	import { permTestData } from '$nobel/data';
	import { replicationSourceUrl } from '$lib/reading/replicationSource';
	import { BARE_CLASS, useBareChrome } from '$lib/reading/brandChrome';

	// Branded in the main text; bare in the Additional Information pane.
	const bare = useBareChrome();

	type PanelSpec = { key: string; label: string; subtitle?: string };

	let {
		number,
		caption,
		panels,
		note
	}: { number?: string; caption?: string | null; panels?: PanelSpec[]; note?: string } = $props();

	// Default: the two "good match" samples (Figure 3 in the main text). The
	// appendix "more groups" figure passes its own panel set (the professor /
	// non-professor / weak-match definitions) via the `panels` prop.
	const DEFAULT_PANELS: PanelSpec[] = [
		{
			key: 'good_nonecon_sample',
			label: 'Panel A: Chem / Physics / Medicine'
		},
		{
			key: 'good_econ_sample',
			label: 'Panel B: All fields including Economics'
		}
	];
	let PANELS: PanelSpec[] = $derived(panels ?? DEFAULT_PANELS);

	// `selected` is null until the user picks a tab, at which point it pins the
	// active key; otherwise the first panel is active. Derived so it stays valid
	// even if the `panels` prop differs from the default set.
	let selected = $state<string | null>(null);
	let activePanel = $derived(selected ?? PANELS[0].key);
	let host: HTMLDivElement;
	let controlsEl: HTMLDivElement;
	let redraw: () => void = () => {};

	let currentStats = $derived(() => {
		const e = permTestData.data[activePanel];
		return { n: e.n, excess: e.excess_rate, p: e.p_value_display };
	});

	onMount(() => {
		const margin = { top: 24, right: 24, bottom: 56, left: 64 };
		const height = 280;

		const cc = createChartContainer(host, {
			title: caption ?? undefined,
			source: 'parent_field_match/parent_field_perm_test.py',
			sourceUrl: replicationSourceUrl('parent_field_match/parent_field_perm_test.py'),
			showBranding: !bare,
			className: bare ? BARE_CLASS : ''
		});

		// Fold "Figure N" into the title as a small-caps label, and move the
		// panel toggle + stats chip into the header below the title,
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

			const entry = permTestData.data[activePanel];
			const hist = entry.sim_histogram;
			if (!hist || hist.length === 0) return;

			// Infer bin width from bin centers
			const binWidth = hist.length > 1 ? hist[1].bin_center - hist[0].bin_center : 0.04;
			const xMin = hist[0].bin_center - binWidth / 2;
			const xMax = hist[hist.length - 1].bin_center + binWidth / 2;
			const yMax = Math.max(...hist.map((b) => b.fraction));

			const xScale = createLinearScale({
				domain: [xMin, Math.max(xMax, entry.observed_share + binWidth)],
				range: [0, innerWidth]
			});
			const yScale = createLinearScale({
				domain: [0, yMax * 1.18],
				range: [innerHeight, 0]
			});

			createYAxis(chartArea, yScale, {
				x: 0,
				grid: true,
				gridWidth: innerWidth,
				tickCount: 4,
				labelX: -45,
				label: 'Fraction of simulations'
			});
			createXAxis(chartArea, xScale, {
				y: innerHeight,
				tickFormat: d3.format('.0%'),
				tickCount: Math.max(2, Math.floor(innerWidth / 45)),
				label: 'Parent-child field match share'
			});

			// Simulation histogram bars
			const barW = Math.max((xScale(xMin + binWidth) - xScale(xMin)) - 1, 1);
			type HistBin = (typeof hist)[0];
			chartArea
				.append('g')
				.selectAll('rect')
				.data(hist)
				.join('rect')
				.attr('x', (b: HistBin) => xScale(b.bin_center - binWidth / 2))
				.attr('y', (b: HistBin) => yScale(b.fraction))
				.attr('width', barW)
				.attr('height', (b: HistBin) => Math.max(innerHeight - yScale(b.fraction), 0))
				.attr('fill', '#b0bec5')
				.attr('stroke', 'white')
				.attr('stroke-width', 0.5);

			// Observed line
			const obsX = xScale(entry.observed_share);
			chartArea
				.append('line')
				.attr('x1', obsX).attr('x2', obsX)
				.attr('y1', 0).attr('y2', innerHeight)
				.attr('stroke', '#d62728')
				.attr('stroke-width', 2);

			// Label the observed line
			chartArea
				.append('text')
				.attr('x', innerWidth - 4)
				.attr('text-anchor', 'end')
				.attr('y', 14)
				.attr('font-size', '11px')
				.attr('fill', '#d62728')
				.text(`Observed: ${entry.observed_pct.toFixed(1)}% (p ${entry.p_value_display})`);

			// Expected (simulation mean) line
			const expX = xScale(entry.sim_mean);
			chartArea
				.append('line')
				.attr('x1', expX).attr('x2', expX)
				.attr('y1', 0).attr('y2', innerHeight)
				.attr('stroke', '#555')
				.attr('stroke-width', 1)
				.attr('stroke-dasharray', '4,3');

			chartArea
				.append('text')
				.attr('x', 4)
				.attr('y', 26)
				.attr('text-anchor', 'start')
				.attr('font-size', '11px')
				.attr('fill', '#555')
				.text(`Expected: ${(entry.sim_mean * 100).toFixed(1)}%`);
		}

		redraw = render;
		render();
		const stopObserving = observeChartWidth(container.node(), svg, dimensions, render);

		const noteEl = document.createElement('p');
		noteEl.className = 'ddl-chart-note';
		noteEl.textContent =
			note ??
			'Grey bars: distribution of parent-child field match shares across 10,000 random reassignments. Dashed line: simulation mean (expected under null). Red line: empirically observed match share. p-value = fraction of simulations ≥ observed.';
		cc.container.insertBefore(noteEl, cc.footer);

		return () => {
			stopObserving();
			container.dispatch('remove');
			host.replaceChildren();
		};
	});

	function onPanelChange(key: string) {
		selected = key;
		redraw();
	}

</script>

<figure class="viz-figure">
	<div class="chart-controls ui" bind:this={controlsEl}>
		<div class="tab-strip" role="tablist" aria-label="Sample">
			{#each PANELS as p (p.key)}
				<button
					role="tab"
					aria-selected={activePanel === p.key}
					class:active={activePanel === p.key}
					onclick={() => onPanelChange(p.key)}
				>
					{p.label}
					{#if p.subtitle}<span class="tab-sub">{p.subtitle}</span>{/if}
				</button>
			{/each}
		</div>
		{#if currentStats}
			{@const s = currentStats()}
			<span class="stats-chip">
				N = {s.n} &nbsp;·&nbsp; excess rate +{s.excess.toFixed(0)}% &nbsp;·&nbsp; p {s.p}
			</span>
		{/if}
	</div>

	<div class="chart-host" bind:this={host} style="min-height:305px"></div>
</figure>

<style>
	.viz-figure {
		margin: 2rem 0;
	}

	.chart-controls {
		display: flex;
		flex-wrap: wrap;
		align-items: flex-start;
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
		text-align: left;
	}

	.tab-strip button.active {
		background: var(--accent);
		color: #fff;
		border-color: var(--accent);
	}

	.tab-sub {
		display: block;
		font-size: 0.72rem;
		opacity: 0.75;
		margin-top: 1px;
	}

	.stats-chip {
		font-size: 0.8rem;
		color: var(--muted);
		font-variant-numeric: tabular-nums;
		align-self: center;
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
