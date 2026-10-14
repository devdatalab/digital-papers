<!--
	FootnoteRef — the inline superscript chip marking a footnote call-out in the
	article prose. Clicking it jumps to the matching note in the section's "Notes"
	list, whose own marker chip jumps back (see SectionBody).

	Deliberately a plain <a> to a same-page hash, not a <button> like
	AnnotationTag: this navigates within the document rather than toggling UI
	state, so it should work without JS, be middle-clickable, and drive the
	:target flash that rings the note on arrival.

	Numbering is passed in rather than derived here — SectionBody owns the
	id → number map, since a number only means anything relative to one section's
	ordered footnotes array.

	DOM ids: the note itself owns `#{id}` (e.g. "#fn3") and this call-out owns
	`#fnref-{id}`, so the two ends of the round trip can each be a scroll target
	without colliding. Only one section renders per page, so section-unique ids
	are page-unique.

	Props:
	  - id: the footnote id (e.g. "fn3"), matching a Footnote in the same section.
	  - number: the reader-facing number to display.
	  - text: plain-text preview from the same content used by the Notes list.

	Hovering the original marker (or focusing it with the keyboard) for 400 ms
	shows a non-interactive preview. Leaving the marker dismisses it immediately;
	the preview never receives pointer events. Click navigation remains native.
	Depends on Svelte lifecycle cleanup and the site's DDL theme tokens.

	Styles are global, in $lib/styles/app.css (.footnote-chip / .footnote-ref),
	shared with the back-link chip so the two ends of the trip stay identical.
-->
<script lang="ts">
	import { onDestroy } from 'svelte';

	let { id, number, text }: { id: string; number: number; text: string } = $props();
	let marker = $state<HTMLAnchorElement>();
	let preview = $state<HTMLSpanElement>();
	let active = $state(false);
	let open = $state(false);
	let positioned = $state(false);
	let timer: ReturnType<typeof setTimeout> | undefined;

	function dismiss() {
		clearTimeout(timer);
		timer = undefined;
		active = false;
		open = false;
		positioned = false;
	}

	function schedule() {
		dismiss();
		if (!text) return;
		active = true;
		timer = setTimeout(() => {
			timer = undefined;
			open = true;
		}, 400);
	}

	function enter(event: PointerEvent) {
		if (event.pointerType === 'mouse') schedule();
	}

	// Cancel pending previews as well as visible ones when the page moves.
	$effect(() => {
		if (!active) return;
		const onKey = (event: KeyboardEvent) => {
			if (event.key === 'Escape') dismiss();
		};
		window.addEventListener('scroll', dismiss, true);
		window.addEventListener('resize', dismiss);
		window.addEventListener('blur', dismiss);
		window.addEventListener('keydown', onKey);
		return () => {
			window.removeEventListener('scroll', dismiss, true);
			window.removeEventListener('resize', dismiss);
			window.removeEventListener('blur', dismiss);
			window.removeEventListener('keydown', onKey);
		};
	});

	// Measure before revealing the fixed box, keeping it inside the viewport.
	$effect(() => {
		if (!open || !marker || !preview) return;
		const margin = 8;
		const gap = 8;
		const anchor = marker.getBoundingClientRect();
		const box = preview.getBoundingClientRect();
		const left = Math.max(margin, Math.min(anchor.left, window.innerWidth - box.width - margin));
		const below = anchor.bottom + gap;
		const top = below + box.height <= window.innerHeight - margin
			? below
			: Math.max(margin, anchor.top - gap - box.height);
		preview.style.left = `${Math.round(left)}px`;
		preview.style.top = `${Math.round(top)}px`;
		positioned = true;
	});

	onDestroy(dismiss);
</script>

<a
	class="footnote-chip footnote-ref"
	id="fnref-{id}"
	href="#{id}"
	aria-label="Footnote {number}"
	aria-describedby={open ? `fnpreview-${id}` : undefined}
	bind:this={marker}
	onpointerenter={enter}
	onpointerleave={dismiss}
	onpointercancel={dismiss}
	onfocus={schedule}
	onblur={dismiss}
	onclick={dismiss}
	>{number}</a
>

{#if open}
	<span
		class="footnote-preview ui"
		class:positioned
		id="fnpreview-{id}"
		role="tooltip"
		bind:this={preview}>{text}</span
	>
{/if}

<style>
	.footnote-preview {
		position: fixed;
		left: 0;
		top: 0;
		z-index: 20;
		pointer-events: none;
		visibility: hidden;
		box-sizing: border-box;
		width: min(380px, calc(100vw - 16px));
		max-height: calc(100vh - 16px);
		overflow: hidden;
		padding: 0.75rem 0.9rem;
		background: var(--bg, #fff);
		border: 1px solid var(--rule-strong, #d7d7d2);
		border-radius: var(--ddl-border-radius, 4px);
		box-shadow: 0 6px 24px rgba(0, 0, 0, 0.14);
		font-family: var(--font-ui);
		font-size: 0.85rem;
		font-weight: 400;
		line-height: 1.5;
		color: var(--ink-soft, #3a3a3a);
		white-space: normal;
		overflow-wrap: anywhere;
		text-align: left;
	}
	.footnote-preview.positioned {
		visibility: visible;
	}
</style>
