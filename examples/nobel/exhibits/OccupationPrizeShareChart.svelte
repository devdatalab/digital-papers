<!--
	OccupationPrizeShareChart — the "Father occupation across Nobel fields"
	annotation pane. For one selected occupation or group it draws horizontal bars
	of the share whose father falls in that group, across populations: the census
	population, all laureates, and each of the four Nobel fields (Chemistry,
	Economics, Medicine, Physics). This is the interactive companion to Results
	footnote 2 ("largely similar across the different prize categories") and to the
	static supplementary panels A8/A9.

	Two selectors ride in the BrandedFrame controls slot (mirroring
	OccupationRankChart): the classification level (10 broad groups / 24-group / detailed occ1950)
	and the group to display (labelled with its laureate count). Composes
	ddl-charts container/scale primitives + D3 for the bars — ddl-charts ships no
	horizontal-bar primitive; if this recurs, add one upstream.

	Upstream dependencies:
	  - $nobel/data (occPrizeSharesData, OccPrizeLevelId, OccPrizeShareGroup)
	  - @devdatalab/ddl-charts (createContainer, createLinearScale)
	  - $lib/charts/labelFit (row-label measurement for the left gutter)
	  - d3
	  - ./BrandedFrame
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';
	import { createContainer, createLinearScale } from '@devdatalab/ddl-charts';
	import { resolveCanvasFont, maxLabelWidth } from '$lib/charts/labelFit';
	import {
		occPrizeSharesData as data,
		type OccPrizeLevelId,
		type OccPrizeShareGroup
	} from '$nobel/data';
	import BrandedFrame from '$lib/reading/BrandedFrame.svelte';

	let { compact = false }: { compact?: boolean } = $props();

	const LEVELS: { id: OccPrizeLevelId }[] = [
		{ id: 'group_10' }, { id: 'group_25' }, { id: 'occ1950' }
	];
	const FIELDS = data.meta.fields; // ["Chemistry","Economics","Medicine","Physics"]

	// Bar rows, top to bottom. Census + All are visually set apart from the fields.
	const CENSUS_COLOR = '#b0bec5';
	const ALL_COLOR = '#1e88e5';
	const FIELD_COLOR = '#7cb3e0';

	let levelId = $state<OccPrizeLevelId>('occ1950');
	let groupId = $state<string>('75');

	const groups = $derived<OccPrizeShareGroup[]>(data.levels[levelId].groups);
	const selected = $derived(groups.find((g) => g.id === groupId) ?? groups[0]);

	// One row per population, in draw order.
	type Row = { key: string; label: string; value: number; color: string; group: 'ref' | 'field' };
	const rows = $derived<Row[]>([
		{ key: 'census', label: 'Census population', value: selected.census_pct, color: CENSUS_COLOR, group: 'ref' },
		{ key: 'all', label: 'All laureates', value: selected.shares.all, color: ALL_COLOR, group: 'ref' },
		...FIELDS.map((f) => ({
			key: f, label: f, value: selected.shares[f] ?? 0, color: FIELD_COLOR, group: 'field' as const
		}))
	]);

	function groupLabel(g: OccPrizeShareGroup): string {
		return `${g.label} · ${g.laureate_n} laureates`;
	}
	function onLevelChange() {
		groupId = data.levels[levelId].groups[0].id;
	}

	let host: HTMLDivElement;
	let redraw: () => void = () => {};

	// Row labels are right-anchored `LABEL_GAP`px left of the plot's x=0, where the
	// bars start. The ref rows ("Census population" / "All laureates") are pulled a
	// further `REF_OUTDENT`px left so the four field rows read as nested under
	// them. Anchoring at a negative x is what keeps a label off the bars: an
	// earlier version indented the *field* rows to x=+4, i.e. inside the plot, so
	// the bars painted over their last letters.
	const LABEL_PX = 11;
	const LABEL_GAP = 6;
	const REF_OUTDENT = 10;
	const labelX = (row: Row) => -(LABEL_GAP + (row.group === 'ref' ? REF_OUTDENT : 0));

	onMount(() => {
		// Size the left gutter to the widest label as actually painted, rather than
		// a magic number that a wider font could silently overflow. The label set is
		// closed and short (6 fixed strings), so this needs no clamp/truncation —
		// unlike FigureMostCommonOccup, whose labels are data-driven.
		const refFont = resolveCanvasFont(host, LABEL_PX, 600); // ref rows are bold
		const fieldFont = resolveCanvasFont(host, LABEL_PX);
		const refMax = maxLabelWidth(
			rows.filter((r) => r.group === 'ref').map((r) => r.label),
			refFont
		);
		const fieldMax = maxLabelWidth(
			rows.filter((r) => r.group === 'field').map((r) => r.label),
			fieldFont
		);
		const gutter = Math.ceil(Math.max(refMax + REF_OUTDENT, fieldMax) + LABEL_GAP + 2);

		const margin = { top: 8, right: 46, bottom: 28, left: gutter };
		const rowH = 30;
		const height = margin.top + margin.bottom + rows.length * rowH;

		const { container, svg, chartArea, dimensions } = createContainer(d3.select(host), {
			height,
			margin,
			responsive: true,
			onResize: () => redraw()
		});

		// createContainer's `responsive` mode only listens to *window* resize, so it
		// misses width changes that happen without one — here, dragging the aside's
		// resize handle. Observe the host directly and re-fit. (Upstream fix:
		// createContainer should use a ResizeObserver; see NobelRankScatter.)
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

		function render() {
			const { innerWidth, innerHeight } = dimensions;
			chartArea.selectAll('*').remove();

			const xMax = Math.max(1, ...rows.map((r) => r.value));
			const xScale = createLinearScale({ domain: [0, xMax * 1.1], range: [0, innerWidth] });
			const band = innerHeight / rows.length;
			const barH = Math.min(14, band - 12);

			// X gridlines + % ticks
			const ticks = xScale.ticks(4);
			chartArea.append('g').selectAll('line').data(ticks).join('line')
				.attr('x1', (t: number) => xScale(t)).attr('x2', (t: number) => xScale(t))
				.attr('y1', 0).attr('y2', innerHeight)
				.attr('stroke', 'var(--rule, #e7e7e4)').attr('stroke-width', 1);
			chartArea.append('g').selectAll('text').data(ticks).join('text')
				.attr('x', (t: number) => xScale(t)).attr('y', innerHeight + 16)
				.attr('text-anchor', 'middle').attr('font-size', '10px')
				.attr('fill', 'var(--muted, #888)').text((t: number) => `${t}%`);

			rows.forEach((r, i) => {
				const yc = i * band + band / 2;
				const g = chartArea.append('g');

				g.append('text')
					.attr('x', labelX(r)).attr('y', yc)
					.attr('text-anchor', 'end').attr('dominant-baseline', 'middle')
					.attr('font-size', `${LABEL_PX}px`)
					.attr('font-weight', r.group === 'ref' ? 600 : 400)
					.attr('fill', 'var(--ink, #1a1a1a)').text(r.label);

				g.append('rect')
					.attr('x', 0).attr('y', yc - barH / 2)
					.attr('width', Math.max(xScale(r.value), 0)).attr('height', barH)
					.attr('fill', r.color)
					.append('title').text(`${r.label}: ${r.value.toFixed(1)}%`);

				g.append('text')
					.attr('x', xScale(r.value) + 4).attr('y', yc)
					.attr('dominant-baseline', 'middle').attr('font-size', '10px')
					.attr('fill', 'var(--muted, #888)').text(`${r.value.toFixed(1)}%`);
			});
		}

		redraw = render;
		render();

		return () => {
			resizeObserver.disconnect();
			container.dispatch('remove');
			host?.replaceChildren();
		};
	});

	// Redraw when the selection changes (after mount wires `redraw`).
	$effect(() => {
		void levelId;
		void groupId;
		redraw();
	});
</script>

{#snippet controls()}
	<div class="occ-controls ui">
		<label class="occ-field">
			<span>Classification</span>
			<select bind:value={levelId} onchange={onLevelChange}>
				{#each LEVELS as lvl (lvl.id)}
					<option value={lvl.id}>{data.levels[lvl.id].label}</option>
				{/each}
			</select>
		</label>
		<label class="occ-field">
			<span>{levelId === 'occ1950' ? 'Occupation' : 'Occupation group'}</span>
			<select bind:value={groupId}>
				{#each groups as g (g.id)}
					<option value={g.id}>{groupLabel(g)}</option>
				{/each}
			</select>
		</label>
	</div>
{/snippet}

<div class="occ-prize" class:compact>
	<BrandedFrame
		title="Father occupation across Nobel fields"
		{controls}
	>
		<div class="occ-host" bind:this={host}></div>
	</BrandedFrame>
</div>

<style>
	.occ-prize { width: 100%; max-width: 100%; }
	.occ-controls { display: flex; flex-wrap: wrap; gap: 0.75rem 1rem; }
	.occ-field { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.78rem; color: var(--muted); }
	.occ-field > span { font-weight: 600; letter-spacing: 0.02em; }
	.occ-field select {
		font-family: var(--font-ui); font-size: 0.82rem; color: var(--ink);
		padding: 0.35rem 0.6rem; border: 1px solid var(--rule-strong, #ccc);
		border-radius: var(--ddl-border-radius, 4px); background: var(--bg, #fff);
		cursor: pointer; max-width: min(24rem, 88vw);
	}
	.occ-field select:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
	.occ-host { width: 100%; }
</style>
