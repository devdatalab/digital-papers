<!--
  Citation — renders a resolved in-text citation. Clicking it opens a small
  popover showing the full text of the reference(s) it points to, so a reader
  can see the source without scrolling to the (collapsed) reference list at the
  bottom of the page. Falls back to plain text when no reference resolves.

  The popover is anchored at the citation's left edge, then shifted left after
  it opens so its right edge never spills past the reading column (citations
  near the right margin would otherwise overflow the body).
-->
<script lang="ts">
	import type { InlineNode, ReferenceEntry } from '$lib/content';
	let {
		node,
		lookup
	}: {
		node: Extract<InlineNode, { t: 'cite' }>;
		lookup: (refId: string) => ReferenceEntry | undefined;
	} = $props();

	// Every reference this citation points to (text plus, when known, a link-out url).
	const refs = $derived(
		node.refIds.map((id) => lookup(id)).filter((r): r is ReferenceEntry => Boolean(r))
	);
	// Anchor still points at the reference list as a no-JS fallback.
	const href = $derived(node.refIds.length ? `#ref-${node.refIds[0]}` : undefined);

	let open = $state(false);
	let wrapEl = $state<HTMLElement>();
	let popEl = $state<HTMLElement>();

	function toggle(event: MouseEvent) {
		event.preventDefault();
		open = !open;
	}

	// While open, close on an outside click or Escape. The listener is attached
	// after the opening click has finished propagating, so it never sees it.
	$effect(() => {
		if (!open) return;
		const onClick = (e: MouseEvent) => {
			if (wrapEl && !wrapEl.contains(e.target as Node)) open = false;
		};
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') open = false;
		};
		document.addEventListener('click', onClick);
		document.addEventListener('keydown', onKey);
		return () => {
			document.removeEventListener('click', onClick);
			document.removeEventListener('keydown', onKey);
		};
	});

	// Keep the popover within the reading column: shift it left by however much
	// it overflows the article's right edge, without pushing past the left edge.
	$effect(() => {
		if (!open || !popEl || !wrapEl) return;
		const margin = 8;
		popEl.style.left = '0px';
		const bounds = (wrapEl.closest('article') ?? document.documentElement).getBoundingClientRect();
		const rect = popEl.getBoundingClientRect();
		let left = 0;
		if (rect.right > bounds.right - margin) left = bounds.right - margin - rect.right;
		if (rect.left + left < bounds.left + margin) left = bounds.left + margin - rect.left;
		popEl.style.left = `${Math.round(left)}px`;
	});
</script>

{#if refs.length > 0}
	<span class="cite-wrap" bind:this={wrapEl}>
		<a
			class="citation"
			class:active={open}
			{href}
			aria-expanded={open}
			onclick={toggle}>{node.text}</a
		>
		{#if open}
			<span class="popover ui" role="dialog" bind:this={popEl}>
				{#each refs as ref (ref.id)}
					<span class="entry">
						{ref.text}
						{#if ref.url}
							<a class="source" href={ref.url} target="_blank" rel="noopener noreferrer"
								>View source →</a
							>{/if}
					</span>
				{/each}
			</span>
		{/if}
	</span>
{:else}{node.text}{/if}

<style>
	.cite-wrap {
		position: relative;
	}
	.citation {
		color: var(--link, #1a4fc4);
		text-decoration: none;
		border-bottom: 1px dotted currentColor;
		cursor: pointer;
	}
	.citation:hover,
	.citation.active {
		text-decoration: none;
		border-bottom-style: solid;
	}
	.popover {
		position: absolute;
		top: calc(100% + 0.4rem);
		left: 0;
		z-index: 20;
		width: min(340px, 80vw);
		white-space: normal;
		padding: 0.75rem 0.9rem;
		background: var(--bg, #fff);
		border: 1px solid var(--rule-strong, #d7d7d2);
		border-radius: var(--ddl-border-radius, 4px);
		box-shadow: 0 6px 24px rgba(0, 0, 0, 0.14);
		font-size: 0.85rem;
		line-height: 1.5;
		color: var(--ink-soft, #3a3a3a);
		text-align: left;
	}
	.entry {
		display: block;
	}
	.source {
		margin-left: 0.35rem;
		font-size: 0.8rem;
		white-space: nowrap;
		color: var(--link, #1a4fc4);
	}
	.entry + .entry {
		margin-top: 0.6rem;
		padding-top: 0.6rem;
		border-top: 1px solid var(--rule, #e7e7e4);
	}
</style>
