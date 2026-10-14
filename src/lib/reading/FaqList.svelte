<!--
	FaqList: renders a `faq` content block as an accordion of question/answer
	pairs. The first answer starts open; the rest open on demand, so a reader can
	scan the list and read only the answers they care about.

	Each item has a stable `id`, so `#faq-q1` style links deep-link to a question.
	If the URL hash matches an item on load or on hash change, that item opens.

	The component does not render answer content itself. `SectionBody` passes its
	block renderer in as the `answer` snippet, so answers get the same citations,
	annotation tags, footnote refs and cross-references as the rest of the prose.

	Upstream dependencies: the `FaqItem` / `Block` types from $lib/content, and
	the theme tokens (--rule, --ink, --accent, --highlight) from ddl-theme.css
	and app.css.

	Props:
	  - items: FaqItem[] (the question/answer pairs, in display order)
	  - answer: Snippet<[Block[], number]> (renders one answer's blocks; the
	    second argument is the item's index, which SectionBody uses to give
	    answer blocks stable DOM ids for search)
-->
<script lang="ts">
	import { untrack, type Snippet } from 'svelte';
	import type { Block, FaqItem } from '$lib/content';

	let { items, answer }: { items: FaqItem[]; answer: Snippet<[Block[], number]> } = $props();

	// Ids of the currently open items. Kept in state rather than left to the
	// native <details> toggle so a hash navigation can open the target item.
	let open = $state(new Set<string>(untrack(() => items[0] ? [items[0].id] : [])));

	function openFromHash() {
		const id = decodeURIComponent(location.hash.slice(1));
		if (items.some((item) => item.id === id)) open = new Set(open).add(id);
	}

	$effect(() => {
		openFromHash();
		window.addEventListener('hashchange', openFromHash);
		return () => window.removeEventListener('hashchange', openFromHash);
	});

	function onToggle(id: string, e: Event) {
		const isOpen = (e.currentTarget as HTMLDetailsElement).open;
		if (isOpen === open.has(id)) return;
		const next = new Set(open);
		if (isOpen) next.add(id);
		else next.delete(id);
		open = next;
	}
</script>

<div class="faq">
	{#each items as item, i (item.id)}
		<details
			id={item.id}
			class="faq-item"
			open={open.has(item.id)}
			ontoggle={(e) => onToggle(item.id, e)}
		>
			<summary>
				<span class="faq-num ui">Q{i + 1}</span>
				<span class="faq-question">{item.question}</span>
				<a class="faq-anchor" href="#{item.id}" aria-label="Link to this question">#</a>
			</summary>
			<div class="faq-answer">
				{@render answer(item.blocks, i)}
			</div>
		</details>
	{/each}
</div>

<style>
	.faq {
		margin: 2rem 0;
		border-top: 1px solid var(--rule, #e2e2e2);
	}
	.faq-item {
		border-bottom: 1px solid var(--rule, #e2e2e2);
		scroll-margin-top: calc(var(--header-h) + 1.5rem);
	}
	.faq-item > summary {
		cursor: pointer;
		list-style: none;
		display: flex;
		align-items: baseline;
		gap: 0.75rem;
		padding: 1rem 0.25rem;
		user-select: none;
	}
	.faq-item > summary::-webkit-details-marker {
		display: none;
	}
	.faq-item > summary:hover {
		background: var(--highlight, #f6f6f4);
	}
	.faq-num {
		flex: none;
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.06em;
		color: var(--accent);
	}
	.faq-question {
		flex: 1;
		font-family: var(--font-serif);
		font-size: 1rem;
		font-weight: 600;
		line-height: 1.35;
		color: var(--ink);
	}
	/* Disclosure caret, rotated when open. Matches SectionBody's .collapsible. */
	.faq-question::before {
		content: '';
		display: inline-block;
		vertical-align: middle;
		margin-right: 0.6rem;
		width: 0;
		height: 0;
		border-left: 5px solid currentColor;
		border-top: 4px solid transparent;
		border-bottom: 4px solid transparent;
		transition: transform 0.15s ease;
	}
	.faq-item[open] .faq-question::before {
		transform: rotate(90deg);
	}
	.faq-anchor {
		flex: none;
		color: var(--muted, #888);
		opacity: 0;
		text-decoration: none;
		transition: opacity 0.15s ease;
	}
	.faq-item > summary:hover .faq-anchor,
	.faq-anchor:focus-visible {
		opacity: 1;
	}
	.faq-answer {
		font-size: 1rem;
		padding: 0 0.25rem 1rem 2.5rem;
	}
	@media (max-width: 640px) {
		.faq-answer {
			padding-left: 0.25rem;
		}
	}
</style>
