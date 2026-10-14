<!--
	AnnotationPanel — the single card in the right-hand "Additional Information"
	pane, rendered by +layout.svelte for the one id currently open in
	annotationStack. Shows the tag, a title/subtitle, and a small body
	(paragraphs, images, or an interactive appendix figure/table resolved via
	appendixRegistry) looked up via getAnnotation. Closeable; opening another
	tag replaces this panel rather than stacking beside it.

	Props:
	  - id: the annotation tag id (e.g. "A1") to render.
-->
<script lang="ts">
	import { base } from '$app/paths';
	import { getAnnotation, getAnnotationLocation } from '$lib/content';
	import { annotationStack } from '$lib/state/annotationStack.svelte';
	import { panels as appendixComponents } from '$paper/exhibits';
	import { setBareChrome } from './brandChrome';

	// Every appendix figure/table passes through this panel, so this is the one
	// place that has to declare it: no DDL brand wrapper on anything in the pane.
	// The card below already supplies the border and heading. See ./brandChrome.
	setBareChrome();

	let { id, currentSectionId }: { id: string; currentSectionId: string } = $props();

	const entry = $derived(getAnnotation(id));
	// Where this annotation's inline tag lives (undefined if it's never tagged in
	// prose). Same href shape as SectionBody's xref links: an in-page hash for the
	// current section, else a base-prefixed cross-section link — SvelteKit handles
	// navigate-then-scroll to the #annotation-{id} target.
	const jumpTarget = $derived(getAnnotationLocation(id));
	const jumpHref = $derived(
		jumpTarget
			? `${jumpTarget === currentSectionId ? '' : `${base}/${jumpTarget}`}#annotation-${id}`
			: undefined
	);
</script>

{#if entry}
	<article class="annotation-panel ui">
		<header>
			<button
				type="button"
				class="tag"
				aria-label="Close supplementary info: {entry.title}"
				onclick={() => annotationStack.close(id)}
			>
				{entry.id}
			</button>
			<div class="heading">
				<h3>
					<button
						type="button"
						class="title-close"
						aria-label="Close supplementary info: {entry.title}"
						onclick={() => annotationStack.close(id)}
					>
						{entry.title}
					</button>
				</h3>
				<p class="subtitle">{entry.subtitle}</p>
				{#if jumpHref}
					<a class="show-in-text" href={jumpHref}>Show in text ↑</a>
				{/if}
			</div>
			<button
				type="button"
				class="close"
				aria-label="Close supplementary info: {entry.title}"
				onclick={() => annotationStack.close(id)}
			>
				&times;
			</button>
		</header>
		<div class="body">
			{#each entry.body as block, i (i)}
				{#if block.type === 'paragraph'}
					<p>
						{#if block.nodes}
							{#each block.nodes as node}
								{#if node.t === 'emph'}<em>{node.text}</em>{:else}{node.text}{/if}
							{/each}
						{:else}
							{block.text}
						{/if}
					</p>
				{:else if block.type === 'image'}
					<figure>
						<img src="{base}/{block.src}" alt={block.alt} />
						{#if block.caption}
							<figcaption>{block.caption}</figcaption>
						{/if}
					</figure>
				{:else if block.type === 'component'}
					{@const Cmp = appendixComponents[block.component]}
					{#if Cmp}
						<div class="component-block">
							<Cmp {...block.props ?? {}} />
						</div>
					{:else}
						<p class="component-missing">
							Interactive content unavailable (unknown component “{block.component}”).
						</p>
					{/if}
				{/if}
			{/each}
		</div>
	</article>
{/if}

<style>
	.annotation-panel {
		background: var(--bg, #fff);
		border: 1px solid var(--rule-strong, #d7d7d2);
		border-radius: var(--ddl-border-radius, 4px);
		box-shadow: var(--ddl-shadow-light, 0 2px 8px rgba(0, 0, 0, 0.08));
		overflow: hidden;
	}
	header {
		display: flex;
		align-items: flex-start;
		gap: 0.6rem;
		padding: 0.85rem 0.9rem;
		border-bottom: 1px solid var(--rule, #e7e7e4);
	}
	.tag {
		flex: none;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 1.6rem;
		height: 1.6rem;
		padding: 0;
		border: none;
		border-radius: 50%;
		background: var(--accent-annotation, #e8871e);
		color: #fff;
		font-family: var(--font-ui, inherit);
		font-size: 0.7rem;
		font-weight: 700;
		line-height: 1;
		cursor: pointer;
		/* Same white-gap + accent outer ring as the active in-text AnnotationTag,
		   so the open panel's badge reads as the lit-up counterpart of the badge
		   the reader clicked in the prose. */
		box-shadow: 0 0 0 2px var(--bg, #fff), 0 0 0 4px var(--accent-annotation, #e8871e);
		transition: transform var(--ddl-transition-fast, 0.15s ease);
		/* Nudge in from the card edge so the 4px ring clears the header padding. */
		margin: 2px 0 0 2px;
	}
	.tag:hover {
		transform: scale(1.08);
	}
	.heading {
		flex: 1;
		min-width: 0;
	}
	.heading h3 {
		margin: 0 0 0.2rem;
		font-family: var(--font-serif, inherit);
		font-size: 0.95rem;
		font-weight: 600;
		color: var(--ink, #1a1a1a);
		line-height: 1.3;
	}
	.title-close {
		display: inline;
		margin: 0;
		padding: 0;
		border: none;
		background: none;
		font: inherit;
		color: inherit;
		text-align: left;
		cursor: pointer;
	}
	.title-close:hover {
		text-decoration: underline;
	}
	.subtitle {
		margin: 0;
		font-size: 0.78rem;
		color: var(--muted, #999);
		line-height: 1.4;
	}
	.show-in-text {
		display: inline-block;
		margin-top: 0.35rem;
		font-family: var(--font-ui, inherit);
		font-size: 0.75rem;
		font-weight: 500;
		color: var(--accent-annotation, #e8871e);
	}
	.show-in-text:hover {
		text-decoration: underline;
	}
	.close {
		flex: none;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 1.7rem;
		height: 1.7rem;
		border: none;
		background: transparent;
		color: var(--muted, #999);
		font-size: 1.55rem;
		font-weight: 700;
		line-height: 1;
		cursor: pointer;
		border-radius: var(--ddl-border-radius, 4px);
	}
	.close:hover {
		background: var(--ddl-color-hover, rgba(0, 0, 0, 0.05));
		color: var(--ink, #1a1a1a);
	}
	.body {
		padding: 0.9rem;
		font-size: 0.85rem;
		line-height: 1.55;
		color: var(--ink-soft, #3a3a3a);
	}
	.body p {
		margin: 0 0 0.75rem;
	}
	.body p:last-child {
		margin-bottom: 0;
	}
	.body figure {
		margin: 0 0 0.75rem;
	}
	.body figure:last-child {
		margin-bottom: 0;
	}
	.body img {
		display: block;
		width: 100%;
		border-radius: var(--ddl-border-radius, 4px);
		border: 1px solid var(--rule, #e7e7e4);
	}
	.body figcaption {
		margin-top: 0.4rem;
		font-size: 0.75rem;
		color: var(--muted, #999);
	}
	/* Interactive appendix figure/table. These render bare (no DDL wrapper — see
	   ./brandChrome), so they sit on the card's own text margin and line up with
	   the paragraphs and heading above them. They used to bleed to the card edges
	   to claw back the width the wrapper's 24px padding cost; with the wrapper
	   gone that padding is gone too, so the content is wider here than it was
	   bleeding, and flush against the border is not worth the remaining pixels.

	   overflow-x still guards a viz with no scroller of its own (wide tables
	   bring their own) so nothing forces the whole page to scroll sideways. */
	.component-block {
		margin: 0 0 0.75rem;
		overflow-x: auto;
	}
	.component-block:last-child {
		margin-bottom: 0;
	}
	.component-missing {
		font-size: 0.78rem;
		font-style: italic;
		color: var(--muted, #999);
	}
</style>
