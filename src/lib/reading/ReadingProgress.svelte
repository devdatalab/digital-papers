<!--
	ReadingProgress — a quiet indicator of scroll position on the current page.
	Lives at the bottom edge of the shared sticky header without affecting layout.
	Uses Svelte lifecycle hooks, SvelteKit navigation, and the site's theme tokens.
	Recalculates after navigation and content resizing (images, expanded blocks).
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import { afterNavigate } from '$app/navigation';

	let progress = $state(0);
	let scheduleUpdate = () => {};

	afterNavigate(() => scheduleUpdate());

	onMount(() => {
		let frame = 0;
		const update = () => {
			frame = 0;
			const distance = document.documentElement.scrollHeight - window.innerHeight;
			progress = distance > 0 ? Math.min(1, Math.max(0, window.scrollY / distance)) : 0;
		};
		scheduleUpdate = () => {
			if (!frame) frame = requestAnimationFrame(update);
		};

		window.addEventListener('scroll', scheduleUpdate, { passive: true });
		window.addEventListener('resize', scheduleUpdate);
		const observer = new ResizeObserver(scheduleUpdate);
		observer.observe(document.body);
		scheduleUpdate();

		return () => {
			window.removeEventListener('scroll', scheduleUpdate);
			window.removeEventListener('resize', scheduleUpdate);
			observer.disconnect();
			cancelAnimationFrame(frame);
			scheduleUpdate = () => {};
		};
	});
</script>

<div class="reading-progress" aria-hidden="true" style:transform="scaleX({progress})"></div>

<style>
	.reading-progress {
		position: absolute;
		inset: auto 0 -1px;
		height: 3px;
		background: var(--accent);
		transform-origin: left;
		pointer-events: none;
	}
</style>
