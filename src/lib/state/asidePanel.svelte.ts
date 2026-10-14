/**
 * asidePanel — shared geometry + open/closed state for the right-hand
 * "Additional Information" aside.
 *
 * Why it exists: the aside lives in the persistent root layout, but its width
 * and collapsed state must be reachable from (a) the drag handle and reopen tab
 * in that layout and (b) AnnotationTag deep inside a routed page (so clicking a
 * tag can re-expand a collapsed aside). Module-level Svelte 5 rune state is the
 * simplest shared store across those unrelated component trees — the same
 * pattern as annotationStack.svelte.ts. Because +layout.svelte never unmounts
 * between routes, the chosen width/collapsed state survives in-session
 * navigation and resets only on a full page reload (intentional: no
 * persistence).
 *
 * Upstream dependency: none (consumed by +layout.svelte, AnnotationTag.svelte).
 */

export const ASIDE_MIN_WIDTH = 300;
export const ASIDE_MAX_WIDTH = 640;
export const ASIDE_DEFAULT_WIDTH = 420;
/** Dragging narrower than this collapses the panel instead of shrinking it. */
export const ASIDE_COLLAPSE_AT = 240;

const clamp = (px: number) => Math.min(ASIDE_MAX_WIDTH, Math.max(ASIDE_MIN_WIDTH, px));

let width = $state(ASIDE_DEFAULT_WIDTH);
let collapsed = $state(false);

export const asidePanel = {
	get width() {
		return width;
	},
	get collapsed() {
		return collapsed;
	},
	expand() {
		collapsed = false;
	},
	collapse() {
		collapsed = true;
	},
	toggle() {
		collapsed = !collapsed;
	},
	/**
	 * Set the in-grid width from a drag. Requests below ASIDE_COLLAPSE_AT
	 * collapse the panel rather than setting a sub-min width; anything else is
	 * clamped into [MIN, MAX] and expands the panel.
	 */
	setWidth(px: number) {
		if (px < ASIDE_COLLAPSE_AT) {
			collapsed = true;
			return;
		}
		collapsed = false;
		width = clamp(px);
	}
};
