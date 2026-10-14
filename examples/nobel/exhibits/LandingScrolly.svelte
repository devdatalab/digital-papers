<!--
	LandingScrolly — the title page's scroll-driven walkthrough of the feature
	chart.

	Why it exists: a first-time reader lands on the title and abstract, then
	scrolls into the paper's central figure. Rather than dropping them in front
	of a dense scatter with controls, this pins the chart in the main column
	beside the navigation and scrolls short step cards over it. Each step changes what the
	chart shows (grey dots → one laureate and her card → field colours and within-country
	rank → global rank → free exploration), so
	the reader learns to read it one idea at a time.

	Layout: a sticky, viewport-height graphic, with the step column pulled up
	over it by a negative margin. Cards sit at the left over the sparse early
	years. On phones (≤719px, the layout's mobile breakpoint) the whole scrolly
	is hidden and the title page shows its own "Introduction" link instead. The step column ignores the pointer
	except on the cards themselves, so the chart stays hoverable in the explore
	step.

	Step text and the per-step chart state live in $paper/content/landing.json;
	this component only maps the active step onto NobelRankScatter's props. The
	metric follows the scroll in the narrated steps; the explore step omits
	`metric`, so whatever the reader picks with the pills is kept.

	The last step is the free-play step and the page's end. It gets no card
	(nothing covers the chart once the reader can use it); instead any closing text and
	the `finale` snippet (the page's "Introduction" button and credits) fade in in a row
	pinned under the chart. That row's height is reserved in every step, so the
	chart never resizes mid-scroll. Nothing follows the scrolly, so at the
	bottom of the page the chart and the button are on screen together.

	The optional `cue` snippet (the page's scroll cue) is overlaid on that same
	row while it is empty, i.e. in every step but the last. Being inside the
	sticky frame, it travels with the chart as it scrolls in rather than
	floating over it.

	Upstream dependencies:
	  - $lib/content (landing: steps, metric keys and pill labels)
	  - $lib/actions/scrollSteps (active-step detection)
	  - NobelRankScatter (the chart itself)
-->
<script lang="ts">
	import type { Snippet } from 'svelte';
	import { landing } from '$nobel/content/read-landing';
	import { scrollSteps } from '$lib/actions/scrollSteps';
	import NobelRankScatter from './NobelRankScatter.svelte';

	// `finale` is rendered in the free-play row and `cue` over it until the
	// last step (the page owns navigation). `active` is bindable so the page's
	// cue can advance to the next step.
	// -1 = the reader hasn't reached the first step yet (the chart is still
	// scrolling into view); it shows the first step's state meanwhile.
	let {
		finale,
		cue,
		active = $bindable(-1)
	}: { finale?: Snippet; cue?: Snippet; active?: number } = $props();

	const steps = landing.steps;

	let metric = $state(steps[0]?.chart.metric ?? landing.metrics[0]);
	const view = $derived(steps[Math.max(active, 0)].chart);
	const lastIndex = steps.length - 1;
	const playing = $derived(active === lastIndex);

	function onStep(i: number) {
		active = i;
		const m = steps[Math.max(i, 0)]?.chart.metric;
		if (m) metric = m;
	}
</script>

<section class="scrolly" id="explore" aria-label="Guided tour of the Nobel laureates chart">
	<div class="graphic">
		<div class="frame">
			<NobelRankScatter
				fill
				bind:metric
				metricKeys={landing.metrics}
				metricLabels={landing.metricLabels}
				colorMode={view.color}
				focusId={view.focus}
				focusCard={view.card ?? false}
				highlightFrom={view.highlightFrom ?? null}
				controls={view.controls}
			/>
			<div class="play" class:on={playing} aria-hidden={!playing}>
				{#if steps[lastIndex].text}<p>{steps[lastIndex].text}</p>{/if}
				{#if finale}{@render finale()}{/if}
			</div>
			{#if cue}
				<div class="cue" class:off={playing} aria-hidden={playing}>{@render cue()}</div>
			{/if}
		</div>
	</div>

	<div class="steps" use:scrollSteps={{ onStep }}>
		{#each steps as step, i (step.id)}
			<div class="step" data-step>
				{#if i !== lastIndex}
					<p class="card" class:active={i === active}>{step.text}</p>
				{/if}
			</div>
		{/each}
	</div>
</section>

<style>
	.scrolly {
		position: relative;
	}

	/* The pinned chart: exactly one viewport tall below the sticky site header.
	   svh (not vh) so the frame doesn't jump as mobile browser toolbars
	   show and hide. */
	.graphic {
		position: sticky;
		top: var(--header-h);
		height: calc(100svh - var(--header-h));
		padding: 1rem 0 1.5rem;
		background: var(--bg);
		box-sizing: border-box;
	}
	/* Chart above, free-play row below; the chart takes what the row leaves. */
	.frame {
		position: relative;
		height: 100%;
		max-width: 1600px;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
	}
	.frame > :global(.nobel-viz) {
		flex: 1 1 0;
		min-height: 0;
	}

	/* Free-play block: instructions stacked over "Introduction", centered.
	   Always laid out (so the chart height is stable) but invisible until the
	   last step. */
	.play {
		flex: none;
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		gap: 0.6rem;
		/* Keep the chart's x-axis title clear of the text below it. */
		margin-top: 1.25rem;
		padding-top: 1rem;
		opacity: 0;
		visibility: hidden;
		transition:
			opacity 0.25s ease,
			visibility 0s linear 0.25s;
	}
	.play.on {
		opacity: 1;
		visibility: visible;
		transition: opacity 0.25s ease;
	}
	.play p {
		max-width: 44rem;
		margin: 0;
		font-size: 0.9rem;
		line-height: 1.5;
		color: var(--ink-soft);
	}

	/* Scroll cue, overlaid at the foot of the (still empty) free-play row;
	   hidden on the last step, when that row fills. */
	.cue {
		position: absolute;
		left: 0;
		right: 0;
		bottom: 0;
		display: flex;
		justify-content: center;
		pointer-events: none;
		transition:
			opacity 0.25s ease,
			visibility 0s;
	}
	.cue > :global(*) {
		pointer-events: auto;
	}
	.cue.off {
		opacity: 0;
		visibility: hidden;
		transition:
			opacity 0.25s ease,
			visibility 0s linear 0.25s;
	}

	/* Step column, pulled up so it scrolls over the pinned chart. */
	.steps {
		position: relative;
		z-index: 1;
		margin-top: calc(-1 * (100svh - var(--header-h)));
		pointer-events: none;
	}
	.step {
		min-height: 100svh;
		display: flex;
		align-items: center;
		/* Follow the centered chart's plot area, reducing the inset when the
		   main column is narrow so the cards still fit beside the navigation. */
		padding: 0 max(0px, calc((100% - 1600px) / 2)) 0
			calc(max(0px, calc((100% - 1600px) / 2)) + clamp(1rem, 10%, 100px));
		box-sizing: border-box;
	}

	.card {
		pointer-events: auto;
		box-sizing: border-box;
		min-width: 0;
		width: 100%;
		max-width: 22rem;
		margin: 0;
		padding: 1.1rem 1.3rem;
		font-size: 1.05rem;
		line-height: 1.55;
		color: var(--ink);
		background: color-mix(in srgb, var(--bg, #fff) 94%, transparent);
		backdrop-filter: blur(4px);
		border: 1px solid var(--rule);
		border-radius: 8px;
		box-shadow: 0 4px 18px rgba(0, 0, 0, 0.08);
		opacity: 0.35;
		transition: opacity 0.2s ease;
	}
	.card.active {
		opacity: 1;
	}

	/* Phones: no scrolly at all. A full-viewport pinned chart with cards over
	   it is too cramped to read at this width, so the title page offers
	   "Introduction" directly instead (see +page.svelte). Hidden with CSS
	   rather than an {#if} so the prerendered page doesn't flash the chart
	   before hydration; the chart still mounts but skips zero-width resizes. */
	@media (max-width: 719px) {
		.scrolly {
			display: none;
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.card,
		.play,
		.play.on,
		.cue,
		.cue.off {
			transition: none;
		}
	}
</style>
