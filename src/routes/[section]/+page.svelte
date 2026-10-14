<!--
	Section page — renders one top-level section of the paper in the centre
	reading column, with previous/next navigation to adjacent sections.
-->
<script lang="ts">
	import { base } from '$app/paths';
	import { meta } from '$lib/content';
	import SectionBody from '$lib/reading/SectionBody.svelte';
	import RefereeResponses from '$lib/reading/RefereeResponses.svelte';
	import { pages } from '$paper/exhibits';
	import type { PageData } from './$types';

	let { data, submission = 1 }: { data: PageData; submission?: number } = $props();

	let isRevision = $derived(
		['referee-comments-and-responses', 'faq'].includes(data.section.id)
	);
</script>

<svelte:head>
	<title>{data.section.number}. {data.section.title} — {meta.title}</title>
</svelte:head>

{#if pages[data.section.id]}
	{@const Explorer = pages[data.section.id]}
	<Explorer />
{:else}
<article class="section">
	<header class="section-head" class:compact={data.section.id === 'referee-comments-and-responses'}>
		<p class="kicker ui">
			{#if isRevision}Revisions and FAQ{:else}Section {data.section.number}{/if}
		</p>
		<h1>{data.section.title}</h1>
	</header>

	{#if data.section.id === 'referee-comments-and-responses'}
		<RefereeResponses {submission} />
	{:else}
		<SectionBody section={data.section} />
	{/if}

	<nav class="pager ui" aria-label="Section navigation">
		{#if data.prev}
			<a class="prev" href="{base}/{data.prev.id}">
				<span class="dir">← Previous</span>
				<span class="t">{data.prev.number}. {data.prev.title}</span>
			</a>
		{:else}
			<a class="prev" href="{base}/">
				<span class="dir">← Previous</span>
				<span class="t">Title &amp; abstract</span>
			</a>
		{/if}

		{#if data.next}
			<a class="next" href="{base}/{data.next.id}">
				<span class="dir">Next →</span>
				<span class="t">{data.next.number}. {data.next.title}</span>
			</a>
		{/if}
	</nav>

	{#if data.section.references.length > 0}
		<details class="references ui">
			<summary>References ({data.section.references.length})</summary>
			<ol>
				{#each data.section.references as ref (ref.id)}
					<li id="ref-{ref.id}">
						{ref.text}
						{#if ref.url}
							<a class="source" href={ref.url} target="_blank" rel="noopener noreferrer"
								>View source →</a
							>
						{/if}
					</li>
				{/each}
			</ol>
		</details>
	{/if}
</article>

{/if}

<style>
	.section {
		max-width: var(--read-max);
		margin: 0;
	}

	.section-head {
		margin-bottom: 2.5rem;
	}
	.section-head.compact {
		margin-bottom: 0.85rem;
	}
	.kicker {
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--accent);
		margin: 0 0 0.6rem;
	}
	.section-head h1 {
		font-family: var(--font-serif);
		font-size: clamp(1.8rem, 3.5vw, 2.4rem);
		line-height: 1.15;
		font-weight: 600;
		color: var(--ink);
		margin: 0;
		letter-spacing: -0.01em;
	}

	.pager {
		display: flex;
		justify-content: space-between;
		gap: 1.5rem;
		margin-top: 4rem;
		padding-top: 1.5rem;
		border-top: 1px solid var(--rule);
	}
	.pager a {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		max-width: 48%;
		color: var(--ink-soft);
	}
	.pager a:hover {
		text-decoration: none;
		color: var(--ink);
	}
	.pager .next {
		text-align: right;
		margin-left: auto;
	}
	.pager .dir {
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--accent);
	}
	.pager .t {
		font-size: 0.95rem;
	}

	/* References — collapsed by default, below the section pager. */
	.references {
		margin-top: 2rem;
		font-size: 0.9rem;
		line-height: 1.6;
		color: var(--ink-soft);
	}
	.references > summary {
		cursor: pointer;
		list-style: none;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--muted);
		user-select: none;
	}
	.references > summary::-webkit-details-marker {
		display: none;
	}
	.references > summary::before {
		content: '';
		width: 0;
		height: 0;
		border-left: 5px solid currentColor;
		border-top: 4px solid transparent;
		border-bottom: 4px solid transparent;
		transition: transform 0.15s ease;
		flex: none;
	}
	.references[open] > summary::before {
		transform: rotate(90deg);
	}
	.references ol {
		margin: 1rem 0 0;
		padding-left: 1.5rem;
	}
	.references li {
		margin-bottom: 0.6rem;
	}
	.references .source {
		margin-left: 0.4rem;
		white-space: nowrap;
	}
</style>
