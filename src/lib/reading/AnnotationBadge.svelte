<!--
	AnnotationBadge — the small colored "A#" chip identifying an annotation.
	Extracted so the aside page index (AsidePageIndex) shows the same badge the
	inline AnnotationTag and the open AnnotationPanel use, without a third copy
	of the badge CSS. Purely presentational: no state, no click behaviour.

	Props:
	  - id: the annotation tag id (e.g. "A1") shown inside the chip.
-->
<script lang="ts">
	let { id }: { id: string } = $props();
</script>

<span class="annotation-badge">{id}</span>

<style>
	.annotation-badge {
		flex: none;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 1.6rem;
		height: 1.6rem;
		border-radius: 50%;
		background: var(--accent-annotation, #e8871e);
		color: #fff;
		font-family: var(--font-ui, inherit);
		font-size: 0.7rem;
		font-weight: 700;
		line-height: 1;
	}
</style>
