<!-- Render selected paper blocks, inline citations, footnotes and registered exhibits.
     Depends on $lib/content, $paper/exhibits and shared reading modules. -->
<script lang="ts">
	import { base } from '$app/paths';
	import type { Section, InlineNode, Block } from '$lib/content';
	import { getFigureOrTableTarget, getSectionTarget } from '$lib/content';
	import { refDisplayText, blockAnchor, inlineText } from '$lib/content/text';
	import Citation from './Citation.svelte';
	import AnnotationTag from './AnnotationTag.svelte';
	import FootnoteRef from './FootnoteRef.svelte';
	import FaqList from './FaqList.svelte';
	import { figures } from '$paper/exhibits';

	let { section }: { section: Section } = $props();

	const lookupRef = (id: string) => section.references.find((r) => r.id === id);

	// Footnotes are stored in document order, so a note's reader-facing number is
	// just its position. Both ends of the round trip read from this one map, so a
	// call-out can't show a number the Notes list disagrees with.
	const footnoteNumbers = $derived(
		new Map(section.footnotes.map((note, i) => [note.id, i + 1]))
	);
	const footnotePreviews = $derived(
		new Map(section.footnotes.map((note) => [note.id, inlineText(note.nodes)]))
	);
</script>

{#snippet inline(nodes: InlineNode[])}
	{#each nodes as node, i (i)}
		{#if node.t === 'text'}{node.text}
		{:else if node.t === 'emph'}<em>{node.text}</em>
		{:else if node.t === 'cite'}<Citation {node} lookup={lookupRef} />
		{:else if node.t === 'link'}<a
				href={node.href}
				target="_blank"
				rel="noopener noreferrer">{node.text}</a
			>
		{:else if node.t === 'route'}<a class="route-link" class:small={node.small} href="{base}/{node.route}">{node.text}</a>
		{:else if node.t === 'ref'}
			{@const target = getFigureOrTableTarget(node.label)}
			{@const sectionTarget = target ? undefined : getSectionTarget(node.label)}
			{@const displayText = refDisplayText(node, nodes[i - 1])}
			{#if target}
				<a
					class="xref"
					href="{target.sectionId === section.id ? '' : `${base}/${target.sectionId}`}#ref-{node.label}"
					>{displayText}</a
				>
			{:else if sectionTarget}
				<a class="xref" href="{base}/{sectionTarget}">{displayText}</a>
			{:else}
				<span class="xref">{displayText}</span>
			{/if}
		{:else if node.t === 'annotation'}<AnnotationTag id={node.id} />
		{:else if node.t === 'fnref'}
			{@const number = footnoteNumbers.get(node.id)}
			{#if number}
				{#key section.id}
					<FootnoteRef id={node.id} {number} text={footnotePreviews.get(node.id) ?? ''} />
				{/key}
			{/if}
		{/if}
	{/each}
{/snippet}

<!-- `path` is the index path of `blocks` within the section; each block's DOM
     id comes from it via `blockAnchor`, which is how search hits find it. -->
{#snippet renderBlocks(blocks: Block[], path: number[])}
	{#each blocks as block, i (i)}
		{@const anchor = blockAnchor([...path, i])}
		{#if block.type === 'paragraph'}
			<p id={anchor} class:omission={block.nodes[0]?.t === 'text' && block.nodes[0].text.startsWith('[Example excerpt:')}>{@render inline(block.nodes)}</p>
		{:else if block.type === 'heading'}
			{#if block.level === 2}
				<h2 id={anchor}><span class="heading-number">{block.number}</span>{block.text}</h2>
			{:else}
				<h3 id={anchor}><span class="heading-number">{block.number}</span>{block.text}</h3>
			{/if}
		{:else if block.type === 'epigraph'}
			<blockquote id={anchor} class="epigraph">
				{block.text}
				<span class="attribution">{block.attribution}</span>
			</blockquote>
		{:else if block.type === 'links'}
			<ul class="links">
				{#each block.items as item (item.href + item.label)}
					<li>
						<a href={item.href} target="_blank" rel="noopener noreferrer">{item.label}</a>
					</li>
				{/each}
			</ul>
		{:else if block.type === 'figure' || block.type === 'table'}
			{@const Exhibit = block.label ? figures[block.label] : undefined}
			<div id={block.label ? `ref-${block.label}` : anchor} class="figure-anchor">
				{#if Exhibit}
					<Exhibit number={block.number} caption={block.caption} />
				{:else}
					<figure class="placeholder">
						<span class="label"
							>{block.number
								? `${block.type === 'figure' ? 'Figure' : 'Table'} ${block.number}`
								: (block.label ?? '')}</span
						>
						{#if block.caption}
							<span class="caption">{block.caption}</span>
						{/if}
						{#if block.source}<img src="{base}/{block.source}" alt={block.caption ?? block.type} style="max-width:100%" />{:else}<span class="pending">Register this exhibit or provide its asset path.</span>{/if}
					</figure>
				{/if}
			</div>
		{:else if block.type === 'collapsible'}
			<details id={anchor} class="collapsible" class:small={block.small} open={!block.collapsed}>
				<summary>{block.title}</summary>
				<div class="collapsible-body">
					{@render renderBlocks(block.blocks, [...path, i])}
				</div>
			</details>
		{:else if block.type === 'faq'}
			{#snippet answer(answerBlocks: Block[], item: number)}
				{@render renderBlocks(answerBlocks, [...path, i, item])}
			{/snippet}
			<FaqList items={block.items} {answer} />
		{/if}
	{/each}
{/snippet}

<div class="prose">
	{@render renderBlocks(section.blocks, [])}
</div>

{#if section.footnotes.length > 0}
	<aside class="footnotes">
		<h4>Notes</h4>
		<ol>
			{#each section.footnotes as note, i (note.id)}
				<li id={note.id}>
					<a
						class="footnote-chip footnote-marker"
						href="#fnref-{note.id}"
						aria-label="Back to footnote {i + 1} in the text">{i + 1}</a
					>
					<span
						>{@render inline(note.nodes)}
						<!-- The back-link to the call-out, in the conventional footnote spot.
						     U+FE0E forces text presentation so iOS doesn't render ↩ as a
						     colour emoji. -->
						<a
							class="footnote-return"
							href="#fnref-{note.id}"
							aria-label="Back to footnote {i + 1} in the text">↩&#xFE0E;</a
						></span
					>
				</li>
			{/each}
		</ol>
	</aside>
{/if}

<style>
	.omission { color: var(--muted); font-size: 0.85rem; border-left: 2px solid var(--rule); padding-left: 1rem; }
	.route-link.small {
		font-size: 0.85em;
	}
	.xref {
		color: var(--muted, #888);
	}
	a.xref {
		text-decoration: underline;
		text-underline-offset: 2px;
		cursor: pointer;
	}
	a.xref:hover {
		color: var(--accent);
	}
	.figure-anchor {
		scroll-margin-top: calc(var(--header-h) + 1.5rem);
	}
	.collapsible {
		margin: 1.5rem 0;
		border: 1px solid var(--rule-strong, #d7d7d2);
		border-radius: 4px;
		background: var(--bg-inset, #f3f1ea);
	}
	.collapsible.small {
		font-size: 0.95em;
	}
	.collapsible > summary {
		cursor: pointer;
		padding: 0.6rem 0.9rem;
		font-weight: 600;
		list-style: none;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		user-select: none;
	}
	.collapsible > summary::-webkit-details-marker {
		display: none;
	}
	.collapsible > summary::before {
		content: '';
		width: 0;
		height: 0;
		border-left: 5px solid currentColor;
		border-top: 4px solid transparent;
		border-bottom: 4px solid transparent;
		transition: transform 0.15s ease;
		flex: none;
	}
	.collapsible[open] > summary::before {
		transform: rotate(90deg);
	}
	.collapsible > summary:hover {
		background: var(--bg-inset-hover, #ebe8df);
	}
	.collapsible-body {
		padding: 0 0.9rem 0.2rem;
	}
</style>
