<!--
	FigureFieldMatch — the paper's Figure A5, restored as four selectable panels.

	Why this file exists:
	    For each father occupation field, compare its prevalence in the census,
	    among all laureates, and among laureates in each Nobel discipline. Preserve
	    all cross-field comparisons rather than displaying only matching pairs.
	    Field and match-definition selectors follow FigurePermTest's sidebar
	    presentation. All definitions use the same replication data and samples.

	Upstream dependencies:
	    $nobel/data (matchSharesData from parent_field_match_shares.json)
	    @devdatalab/ddl-charts container/scale primitives, d3, observeChartWidth
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';
	import { createChartContainer, createContainer, createLinearScale } from '@devdatalab/ddl-charts';
	import { matchSharesData } from '$nobel/data';
	import { replicationSourceUrl } from '$lib/reading/replicationSource';
	import { observeChartWidth } from '$lib/reading/observeChartWidth';
	import { resolveCanvasFont, maxLabelWidth } from '$lib/charts/labelFit';
	import { BARE_CLASS, useBareChrome } from '$lib/reading/brandChrome';

	const bare = useBareChrome();
	const PANELS = [
		{ key: 'physics', label: 'Parent occupation: physics' },
		{ key: 'chemistry', label: 'Parent occupation: chemistry' },
		{ key: 'medicine', label: 'Parent occupation: physiology' },
		{ key: 'economics', label: 'Parent occupation: economics' }
	];
	const DEFINITIONS = [
		{ key: 'good_match', label: 'Professors and non-professors' },
		{ key: 'prof_match', label: 'Professors only' },
		{ key: 'nonprof_match', label: 'Non-professors only' },
		{ key: 'weak_match', label: 'Weaker topical links' }
	];
	let { caption }: { caption?: string | null } = $props();
	let activePanel = $state(PANELS[0].key);
	let activeDefinition = $state(DEFINITIONS[0].key);
	let host: HTMLDivElement;
	let controlsEl: HTMLDivElement;
	let redraw: () => void = () => {};

	onMount(() => {
		const labelPx = 11;
		const labelFont = resolveCanvasFont(host, labelPx);

		// Wrap repeated row-label wording so the sidebar retains room for bars
		// and their percentage/count labels.
		const labelLines = (label: string) => label.endsWith(' laureate share')
			? [label.slice(0, -' laureate share'.length), 'laureate share']
			: [label];
		const labels = matchSharesData.data.good_match_physics.bars.flatMap((bar) => labelLines(bar.label));
		const margin = {
			top: 8,
			right: 96,
			bottom: 44,
			left: Math.ceil(maxLabelWidth(labels, labelFont)) + 10
		};
		const height = 280;
		const cc = createChartContainer(host, {
			title: caption ?? undefined,
			source: 'parent_field_match/parent_field_match_graphs.py',
			sourceUrl: replicationSourceUrl('parent_field_match/parent_field_match_graphs.py'),
			showBranding: !bare,
			className: bare ? BARE_CLASS : ''
		});
		cc.header.appendChild(controlsEl);

		const { container, svg, chartArea, dimensions } = createContainer(d3.select(cc.body), {
			height,
			margin,
			responsive: false
		});

		function render() {
			const panel = matchSharesData.data[`${activeDefinition}_${activePanel}`];
			const { innerWidth, innerHeight } = dimensions;
			chartArea.selectAll('*').remove();
			if (innerWidth <= 0) return;
			const xMax = Math.max(0.1, ...panel.bars.map((bar) => bar.share));
			const xScale = createLinearScale({ domain: [0, xMax * 1.12], range: [0, innerWidth] });
			const band = innerHeight / panel.bars.length;
			const barHeight = 16;
			const ticks = xScale.ticks(4);

			chartArea.append('g').selectAll('line').data(ticks).join('line')
				.attr('x1', (t: number) => xScale(t))
				.attr('x2', (t: number) => xScale(t))
				.attr('y1', 0).attr('y2', innerHeight)
				.attr('stroke', 'var(--rule, #e7e7e4)');
			chartArea.append('g').selectAll('text').data(ticks).join('text')
				.attr('x', (t: number) => xScale(t))
				.attr('y', innerHeight + 16)
				.attr('text-anchor', 'middle')
				.attr('font-size', '10px').attr('fill', 'var(--muted, #888)')
				.text((t: number) => `${t}%`);
			chartArea.append('text')
				.attr('x', innerWidth / 2).attr('y', innerHeight + 34)
				.attr('text-anchor', 'middle').attr('font-size', '10px')
				.attr('fill', 'var(--muted, #888)').text('Percent share');

			panel.bars.forEach((bar, i) => {
				const y = i * band + band / 2;
				const g = chartArea.append('g');
				const lines = labelLines(bar.label);
				const label = g.append('text')
					.attr('x', -8).attr('y', y - (lines.length - 1) * 6)
					.attr('text-anchor', 'end').attr('dominant-baseline', 'middle')
					.attr('font-size', `${labelPx}px`).attr('fill', 'var(--ink)');
				lines.forEach((line, j) => {
					label.append('tspan').attr('x', -8).attr('dy', j === 0 ? 0 : 12).text(line);
				});
				g.append('rect')
					.attr('x', 0).attr('y', y - barHeight / 2)
					.attr('width', xScale(bar.share)).attr('height', barHeight)
					.attr('fill', bar.row_id === 'census' ? '#90a4ae' : bar.row_id === activePanel ? '#1e88e5' : 'var(--bg)')
					.attr('stroke', 'var(--ink-soft)').attr('stroke-width', 0.7);
				g.append('text')
					.attr('x', xScale(bar.share) + 5).attr('y', y)
					.attr('dominant-baseline', 'middle').attr('font-size', '10px')
					.attr('fill', 'var(--ink-soft)')
					.text(`${bar.share.toFixed(2)}%${bar.count === null ? '' : ` (n=${bar.count})`}`);
			});
		}

		redraw = render;
		render();
		const stopObserving = observeChartWidth(container.node(), svg, dimensions, render);
		const note = document.createElement('p');
		note.className = 'ddl-chart-note';
		note.textContent = 'Each bar shows the share of laureates in a Nobel field whose fathers’ occupations are related to the selected parent field, under the selected match definition. The denominator is all laureates in that Nobel field with usable father-occupation data, including fathers with no field match. The overall bar uses all laureates in the sample; the census bar shows the population occupation share. The economics parent-field panel uses prizes awarded from 1969 onward.';
		cc.container.insertBefore(note, cc.footer);

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

	function onDefinitionChange(event: Event) {
		activeDefinition = (event.currentTarget as HTMLSelectElement).value;
		redraw();
	}
</script>

<figure class="viz-figure">
	<div class="chart-controls ui" bind:this={controlsEl}>
		<label class="definition-select">
			<span>Match definition</span>
			<select value={activeDefinition} onchange={onDefinitionChange}>
				{#each DEFINITIONS as definition (definition.key)}
					<option value={definition.key}>{definition.label}</option>
				{/each}
			</select>
		</label>
		<div class="tab-strip" role="tablist" aria-label="Parent occupation field">
			{#each PANELS as panel (panel.key)}
				<button role="tab" aria-selected={activePanel === panel.key}
					class:active={activePanel === panel.key} onclick={() => onPanelChange(panel.key)}>
					{panel.label}
				</button>
			{/each}
		</div>
	</div>
	<div class="chart-host" bind:this={host}></div>
</figure>

<style>
	.viz-figure { margin: 0; }
	.chart-controls { display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.6rem; }
	.definition-select { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.8rem; }
	.definition-select span { color: var(--muted); }
	.definition-select select {
		font-family: var(--font-ui);
		font-size: 0.8rem;
		padding: 0.3rem 0.65rem;
		border: 1px solid var(--rule-strong);
		border-radius: 3px;
		background: var(--bg);
		color: var(--ink-soft);
		cursor: pointer;
		max-width: 100%;
		align-self: flex-start;
	}
	.tab-strip { display: flex; gap: 0.25rem; flex-wrap: wrap; }
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
	.tab-strip button.active { background: var(--accent); color: #fff; border-color: var(--accent); }
	.chart-host { width: 100%; }
	.chart-host :global(.ddl-chart-note) {
		margin: 0;
		font-size: 0.78rem;
		color: var(--muted, #888);
		line-height: 1.5;
		font-family: var(--font-ui);
	}
</style>
