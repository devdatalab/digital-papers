<!--
	AsidePageIndex — the "On this page" index shown in the right-hand Additional
	Information pane when no annotation card is open. Lists every annotation panel
	the current section SURFACES: the ones it DEFINES (section.annotations, in
	numeric order), together with any it only
	REFERENCES via an inline badge but that another section defines (e.g. Data &
	Methods badges the robustness panel A2, which `results` owns).
	Each is a badge + title button that opens the matching card, giving the reader a
	map of the section's supplementary notes instead of an empty pane. Sections that
	surface no annotations show a muted empty line.

	Props:
	  - sectionId: the current section slug, used to look up the section's panels.

	Upstream dependency: getSection, getReferencedAnnotationIds, getAnnotation
	($lib/content), annotationStack, AnnotationBadge.
-->
<script lang="ts">
	import { getSection, getReferencedAnnotationIds, getAnnotation, type AnnotationEntry } from '$lib/content';
	import { annotationStack } from '$lib/state/annotationStack.svelte';
	import AnnotationBadge from './AnnotationBadge.svelte';

	let { sectionId }: { sectionId: string } = $props();

	// Panels defined in this section, in definition order.
	const defined = $derived(getSection(sectionId)?.annotations ?? []);
	// Panels this section only references (badged inline) but another section
	// defines — appended after the defined ones, in first-appearance order, and
	// resolved to their owning entry so we can show the title.
	const referenced = $derived.by(() => {
		const definedIds = new Set(defined.map((a) => a.id));
		return getReferencedAnnotationIds(sectionId)
			.filter((id) => !definedIds.has(id))
			.map((id) => getAnnotation(id))
			.filter((entry): entry is AnnotationEntry => entry !== undefined);
	});
	const annotations = $derived(
		[...defined, ...referenced].sort((a, b) => Number(a.id.slice(1)) - Number(b.id.slice(1)))
	);
</script>

<div class="page-index ui">
	{#if annotations.length > 0}
		<p class="index-label">On this page</p>
		<ul class="index-list">
			{#each annotations as entry (entry.id)}
				<li>
					<button
						type="button"
						class="index-item"
						onclick={() => annotationStack.toggle(entry.id)}
					>
						<AnnotationBadge id={entry.id} />
						<span class="index-title">{entry.title}</span>
					</button>
				</li>
			{/each}
		</ul>
	{:else}
		<p class="index-empty">No supplementary notes in this section.</p>
	{/if}
</div>

<style>
	.page-index {
		padding: 1.25rem;
	}
	.index-label {
		margin: 0 0 0.75rem;
		font-family: var(--font-ui);
		font-size: 0.72rem;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--muted);
	}
	.index-list {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
	}
	.index-item {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		width: 100%;
		padding: 0.5rem 0.55rem;
		border: none;
		border-radius: var(--ddl-border-radius, 4px);
		background: transparent;
		text-align: left;
		cursor: pointer;
	}
	.index-item:hover {
		background: var(--ddl-color-hover, rgba(0, 0, 0, 0.05));
	}
	.index-title {
		min-width: 0;
		font-family: var(--font-serif);
		font-size: 0.85rem;
		line-height: 1.35;
		color: var(--ink);
	}
	.index-empty {
		margin: 0;
		color: var(--muted);
		font-size: 0.85rem;
		font-style: italic;
		line-height: 1.5;
	}
</style>
