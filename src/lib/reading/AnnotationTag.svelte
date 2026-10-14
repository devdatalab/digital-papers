<!--
	AnnotationTag — the inline "A1"-style circular badge dropped into the
	article prose. Clicking it opens (or closes) the matching card in the
	right-hand "Additional Information" panel via the shared annotationStack.

	Deliberately a <button>, not a citation-style <a>: it toggles UI state
	rather than navigating anywhere. Falls back to plain text if its id
	doesn't resolve to a known annotation, mirroring Citation.svelte's
	fallback for an unresolved reference.

	Props:
	  - id: the annotation tag id (e.g. "A1"), looked up via getAnnotation.
-->
<script lang="ts">
	import { getAnnotation } from '$lib/content';
	import { annotationStack } from '$lib/state/annotationStack.svelte';
	import { asidePanel } from '$lib/state/asidePanel.svelte';

	let { id }: { id: string } = $props();

	const entry = $derived(getAnnotation(id));
	const open = $derived(annotationStack.isOpen(id));
</script>

{#if entry}
	<button
		type="button"
		id="annotation-{id}"
		class="annotation-tag"
		class:active={open}
		aria-pressed={open}
		aria-label="{open ? 'Close' : 'Open'} supplementary info: {entry.title}"
		onclick={() => {
			const willOpen = !annotationStack.isOpen(id);
			annotationStack.toggle(id);
			if (willOpen) asidePanel.expand();
		}}
	>
		{id}
	</button>
{:else}
	{id}
{/if}

<style>
	.annotation-tag {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 1.5em;
		height: 1.5em;
		padding: 0 0.35em;
		margin: 0 0.15em;
		border: none;
		border-radius: 50%;
		background: var(--accent-annotation, #e8871e);
		color: #fff;
		font-family: var(--font-ui, inherit);
		font-size: 0.65em;
		font-weight: 700;
		line-height: 1;
		/* Not `middle`: that centers on baseline + half the x-height, which
		   leaves the circle sitting low against serif prose. A small raise
		   from the baseline centers it on the line's visual body instead. */
		vertical-align: 0.1em;
		cursor: pointer;
		transition: transform var(--ddl-transition-fast, 0.15s ease);
		scroll-margin-top: calc(var(--header-h) + 1.5rem);
	}
	.annotation-tag:hover {
		transform: scale(1.12);
	}
	.annotation-tag.active {
		box-shadow: 0 0 0 2px var(--bg, #fff), 0 0 0 4px var(--accent-annotation, #e8871e);
	}
	/* Brief ring when the reader jumps here via the panel's "Show in text"
	   control (hash navigation sets :target on this button). */
	.annotation-tag:target {
		animation: annotation-tag-flash 1.6s ease-out;
	}
	@keyframes annotation-tag-flash {
		0%,
		45% {
			box-shadow: 0 0 0 2px var(--bg, #fff), 0 0 0 5px var(--accent-annotation, #e8871e);
		}
		100% {
			box-shadow: 0 0 0 2px var(--bg, #fff), 0 0 0 0 rgba(232, 135, 30, 0);
		}
	}
</style>
