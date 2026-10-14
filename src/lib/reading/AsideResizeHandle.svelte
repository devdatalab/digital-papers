<!--
	AsideResizeHandle — the draggable divider on the LEFT edge of the
	"Additional Information" aside (wide, in-grid mode only).

	Why it exists: lets the reader set the aside's width by dragging, and
	collapse it by dragging past the threshold. Kept as its own component so
	+layout.svelte stays focused and the pointer/keyboard logic lives in one
	place. Writes width through asidePanel.setWidth (which clamps and collapses
	below ASIDE_COLLAPSE_AT).

	Drag math is a relative delta from where the drag started (start width +
	how far the pointer moved left). This is layout-independent — it does NOT
	assume the aside hugs the viewport's right edge — so it stays correct now
	that the shell centers the reading+aside group on large screens.

	A grip pill sits sticky at mid-viewport so the divider always advertises
	itself as grabbable, even though the hit area spans the full column height.

	Upstream dependency: asidePanel store.
-->
<script lang="ts">
	import {
		asidePanel,
		ASIDE_MIN_WIDTH,
		ASIDE_MAX_WIDTH
	} from '$lib/state/asidePanel.svelte';

	const STEP = 16; // px nudged per arrow keypress

	let dragging = $state(false);
	// Reference point captured at pointer-down: dragging left of startX widens.
	let startX = 0;
	let startWidth = 0;

	function onPointerDown(event: PointerEvent) {
		event.preventDefault();
		dragging = true;
		startX = event.clientX;
		startWidth = asidePanel.width;
		(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
	}

	function onPointerMove(event: PointerEvent) {
		if (!dragging) return;
		// Pointer moving left (clientX < startX) grows the aside.
		asidePanel.setWidth(startWidth + (startX - event.clientX));
	}

	function onPointerUp(event: PointerEvent) {
		dragging = false;
		(event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId);
	}

	function onKeyDown(event: KeyboardEvent) {
		// Left grows the aside (its handle is on the left edge); Right shrinks it.
		if (event.key === 'ArrowLeft') {
			event.preventDefault();
			asidePanel.setWidth(asidePanel.width + STEP);
		} else if (event.key === 'ArrowRight') {
			event.preventDefault();
			asidePanel.setWidth(asidePanel.width - STEP);
		}
	}
</script>

<!-- A focusable separator with aria-valuenow is the WAI-ARIA "window splitter"
	 pattern for a resizer; svelte's a11y lint treats `separator` as
	 non-interactive, so these two rules are knowingly suppressed here. -->
<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div
	class="resize-handle"
	class:dragging
	role="separator"
	aria-orientation="vertical"
	aria-label="Resize additional information panel"
	aria-valuenow={asidePanel.width}
	aria-valuemin={ASIDE_MIN_WIDTH}
	aria-valuemax={ASIDE_MAX_WIDTH}
	tabindex="0"
	onpointerdown={onPointerDown}
	onpointermove={onPointerMove}
	onpointerup={onPointerUp}
	onpointercancel={onPointerUp}
	onkeydown={onKeyDown}
>
	<!-- Always-visible grip, stuck to mid-viewport, so the divider reads as
	     grabbable at rest. The dotted texture is the conventional resize cue. -->
	<span class="grip" aria-hidden="true"></span>
</div>

<style>
	.resize-handle {
		position: absolute;
		top: 0;
		left: -8px;
		width: 16px;
		height: 100%;
		cursor: col-resize;
		z-index: 2;
		touch-action: none;
	}
	/* Full-height hairline over the aside's border-left; transparent at rest,
	   brightens on hover/drag to show the whole drag line. */
	.resize-handle::after {
		content: '';
		position: absolute;
		top: 0;
		left: 8px;
		width: 2px;
		height: 100%;
		background: transparent;
		transition: background var(--ddl-transition-fast, 0.15s ease);
	}
	.resize-handle:hover::after,
	.resize-handle:focus-visible::after,
	.resize-handle.dragging::after {
		background: var(--accent);
	}

	/* The grip pill: sticky so it rides at mid-viewport as the reader scrolls
	   (the handle itself is full-column-height, whose midpoint would otherwise be
	   far off-screen). A single centered column of exactly four dots + a soft
	   raised surface say "drag me". The corners are only lightly rounded to match
	   the rest of the site's squared-off UI chrome. */
	.grip {
		position: sticky;
		top: calc(50vh - 24px);
		display: block;
		width: 12px;
		height: 48px;
		margin: 0 auto;
		border-radius: 3px;
		/* Four dots (--ink-soft, radius ~1.8px) stacked in one centered column,
		   8px apart and centered vertically within the pill. */
		background:
			radial-gradient(circle 1.8px at 50% calc(50% - 12px), var(--ink-soft), transparent 2.2px),
			radial-gradient(circle 1.8px at 50% calc(50% - 4px), var(--ink-soft), transparent 2.2px),
			radial-gradient(circle 1.8px at 50% calc(50% + 4px), var(--ink-soft), transparent 2.2px),
			radial-gradient(circle 1.8px at 50% calc(50% + 12px), var(--ink-soft), transparent 2.2px),
			var(--bg, #fff);
		border: 1px solid var(--rule-strong);
		box-shadow: 0 1px 5px rgba(0, 0, 0, 0.1);
		transition:
			border-color var(--ddl-transition-fast, 0.15s ease),
			box-shadow var(--ddl-transition-fast, 0.15s ease);
	}
	.resize-handle:hover .grip,
	.resize-handle:focus-visible .grip,
	.resize-handle.dragging .grip {
		border-color: var(--accent);
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.14);
	}
	.resize-handle:focus-visible {
		outline: none;
	}
</style>
