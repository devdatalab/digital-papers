/**
 * annotationStack — shared open/closed state for the right-hand "Additional
 * Information" panel, keyed by annotation tag id (e.g. "A1").
 *
 * Why it exists: an AnnotationTag clicked in the article body (rendered deep
 * inside SectionBody, itself inside a routed page) needs to open a panel in
 * the tools column, which lives in the persistent root layout — two places
 * with no parent/child relationship. Module-level Svelte 5 rune state is the
 * simplest way to share that toggle across both without prop-drilling or a
 * context provider. `+layout.svelte` never unmounts between route changes, so
 * the open panel would otherwise persist across navigation; the layout instead
 * calls `clear()` whenever the reader moves to a different section so a panel
 * only stays open on the section it was opened from.
 *
 * Only ONE panel is open at a time: opening a new tag replaces whatever was
 * open rather than stacking, so the tools column never accumulates a pile of
 * cards. `openId` is the currently-open tag id, or null when none is open.
 *
 * Upstream dependency: none (consumed by AnnotationTag.svelte and
 * +layout.svelte / AnnotationPanel.svelte).
 */

let openId = $state<string | null>(null);

export const annotationStack = {
	get openId() {
		return openId;
	},
	isOpen(id: string) {
		return openId === id;
	},
	toggle(id: string) {
		openId = openId === id ? null : id;
	},
	close(id: string) {
		if (openId === id) openId = null;
	},
	/** Close whatever panel is open, if any. Used by the layout to drop the
	 *  panel when the reader navigates to a different section. */
	clear() {
		openId = null;
	}
};
