<!--
	Title page — the publication's landing view, in two movements:
	  1. Hero: title, authors and abstract close to the header, with a cue
	     to scroll. A second copy of the cue rides in the scrolly's pinned chart
	     frame (under the chart), so a cue is on screen through the narrated
	     steps; each click advances one step. It fades out once the free-play
	     step brings in "Introduction".
	  2. LandingScrolly: the feature chart scrolls in, pins, and step cards walk
	     the reader through how to read it before handing over the controls.
	     In the last step the "Introduction" button fades in under the chart,
	     with the credits just below it, so all share the final pinned screen.
	On phones (≤719px) the scrolly and the scroll cue are hidden, and the
	"Introduction" link sits directly under the abstract instead.

	Upstream dependencies:
	  - $lib/content (meta, navEntries, landing copy)
	  - LandingScrolly (and through it NobelRankScatter)
	  - $lib/state/tour (first-visit reading tour, opened on title-page arrival)
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { meta, navEntries } from '$lib/content';
	import { landing } from '$nobel/content/read-landing';
	import LandingScrolly from '$nobel/exhibits/LandingScrolly.svelte';
	import { tour } from '$lib/state/tour.svelte';

	// Welcome first-time desktop visitors as soon as the title page is mounted.
	

	// First numbered section — the target of the "Introduction" button. Read
	// from the manifest rather than hard-coded so it follows the content if the
	// section order ever changes.
	const firstSection = navEntries[0];

	// Scrolly step the reader is on (-1 = still above it).
	let active = $state(-1);

	// From the hero, scroll the chart into view; within the scrolly, bring the
	// next step's (viewport-tall) block to the middle, where scrollSteps'
	// trigger line sits, so each click advances exactly one step.
	function advance() {
		const behavior = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
		if (active < 0) {
			document.getElementById('explore')?.scrollIntoView({ behavior });
			return;
		}
		const steps = document.querySelectorAll<HTMLElement>('#explore [data-step]');
		steps[active + 1]?.scrollIntoView({ behavior, block: 'center' });
	}
</script>

<svelte:head>
	<title>{meta.title} — {meta.subtitle}</title>
	<meta name="description" content={meta.abstract.slice(0, 180)} />
</svelte:head>

<article class="hero">
	<div class="cover">
		<p class="eyebrow ui">Digital edition · {meta.date}</p>
		<h1>{meta.title}</h1>
		<p class="subtitle">{meta.subtitle}</p>

		<ul class="authors ui">
			{#each meta.authors as author (author.name)}
				<li>
					<span class="name">{author.name}</span>
					<span class="affiliation">{author.affiliation}</span>
				</li>
			{/each}
		</ul>

		<section class="abstract">
			<h2 class="ui">Abstract</h2>
			<p>{meta.abstract}</p>
		</section>
	</div>

	{@render cueButton(false)}
</article>

<!-- Phones only: the scrolly (and the button inside it) is hidden there. -->
<div class="mobile-begin">{@render landingFinale()}</div>

<LandingScrolly finale={landingFinale} cue={scrollyCue} bind:active />

{#snippet landingFinale()}
	{@render beginReading()}
	<footer class="acknowledgment ui">
		<p>{#each landing.acknowledgment as part}{#if part.href}<a href={part.href}>{part.text}</a>{:else}{part.text}{/if}{/each}</p>
	</footer>
{/snippet}

<!-- One cue after the abstract and one under the scrolly's pinned chart. -->
{#snippet cueButton(inScrolly: boolean)}
	<button type="button" class="scroll-cue ui" class:in-scrolly={inScrolly} onclick={advance}>
		<span>{landing.scrollCue}</span>
		<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
			<path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
		</svg>
	</button>
{/snippet}
{#snippet scrollyCue()}{@render cueButton(true)}{/snippet}

{#snippet beginReading()}
	{#if firstSection}
		<nav class="pager ui" aria-label="Start reading">
			<a
				class="btn begin"
				href="{base}/{firstSection.id}">{landing.cta} →</a
			>
		</nav>
	{/if}
{/snippet}

<style>
	/* Keep the cover in natural flow so the graph can begin on the first screen.
	   The title route's shell supplies only a small gap below the site header. */
	.hero {
		display: flex;
		flex-direction: column;
		padding: 0 0 1.5rem;
		box-sizing: border-box;
	}
	.cover {
		max-width: 60rem;
		margin: 0 auto;
		text-align: center;
	}

	.eyebrow {
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--accent);
		margin: 0 0 0.5rem;
	}

	h1 {
		font-family: var(--font-serif);
		font-size: clamp(2rem, 4vw, 2.9rem);
		line-height: 1.12;
		font-weight: 600;
		color: var(--ink);
		margin: 0 0 0.5rem;
		letter-spacing: -0.01em;
	}

	.subtitle {
		font-family: var(--font-serif);
		font-style: italic;
		font-size: clamp(1.2rem, 2.4vw, 1.5rem);
		color: var(--ink-soft);
		margin: 0 0 2rem;
	}

	.authors {
		list-style: none;
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		gap: 1.5rem 2.5rem;
		margin: 0 0 2.5rem;
		padding: 1.25rem 0;
		border-top: 1px solid var(--rule);
		border-bottom: 1px solid var(--rule);
	}
	.authors li {
		display: flex;
		flex-direction: column;
		font-size: 0.9rem;
	}
	.authors .name {
		font-weight: 600;
		color: var(--ink);
	}
	.authors .affiliation {
		color: var(--muted);
	}

	/* Abstract: narrower than the cover so it keeps a comfortable measure. */
	.abstract {
		max-width: 46rem;
		margin: 0 auto;
		text-align: left;
	}
	.abstract h2 {
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
		margin: 0 0 1rem;
		padding-bottom: 0.75rem;
		border-bottom: 1px solid var(--rule);
	}
	.abstract p {
		font-size: 1.15rem;
		line-height: 1.7;
		color: var(--ink-soft);
		margin: 0;
	}

	/* Scroll cue: label over a gently bobbing chevron. Also a button: from the
	   hero it scrolls to the chart, in the scrolly it advances one step. */
	.scroll-cue {
		margin: 0 auto;
		padding: 2rem 1rem 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.8rem;
		font-weight: 600;
		letter-spacing: 0.04em;
		color: var(--muted);
		background: none;
		border: none;
		cursor: pointer;
		transition: opacity 0.4s ease;
	}
	.scroll-cue:hover {
		color: var(--accent);
	}
	.scroll-cue svg {
		animation: cue-bob 1.8s ease-in-out infinite;
	}
	/* The scrolly's copy sits in the pinned frame's free-play row, which
	   LandingScrolly positions and fades; no in-flow spacing needed. */
	.scroll-cue.in-scrolly {
		margin: 0;
		padding: 0.5rem 1rem;
	}
	@keyframes cue-bob {
		0%,
		100% {
			transform: translateY(0);
		}
		50% {
			transform: translateY(5px);
		}
	}

	/* "Introduction", rendered in the scrolly's free-play row under the chart. */
	.pager {
		flex: none;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.35rem;
	}
	.pager .begin {
		font-size: 0.95rem;
		padding: 0.55rem 1.25rem;
	}

	/* Credits follow the button inside the pinned finale, also shared by mobile. */
	.acknowledgment {
		max-width: 52rem;
		margin-top: 0.75rem;
		padding: 0.75rem 0 0;
		border-top: 1px solid var(--rule);
		text-align: center;
		font-size: 0.85rem;
		line-height: 1.6;
		color: var(--muted);
	}
	.acknowledgment p {
		margin: 0;
	}

	/* Official supporter marks sit below the thanks and wrap on narrow screens. */

	/* Only shown on phones, where the scrolly is hidden. */
	.mobile-begin {
		display: none;
	}

	/* Phones: no scrolly (see LandingScrolly), so no cue to scroll to it; the
	   hero shrinks to its content and "Introduction" follows the abstract. */
	@media (max-width: 719px) {
		.scroll-cue {
			display: none;
		}
		.mobile-begin {
			display: block;
			padding: 0.5rem 0 3rem;
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.scroll-cue svg {
			animation: none;
		}
		.scroll-cue {
			transition: none;
		}
	}
</style>
