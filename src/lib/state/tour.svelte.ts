/**
 * tour — shared open/step state for the reading tour (ReadingTour.svelte).
 *
 * Why it exists: the tour is started on first arrival at the title page
 * and from the header's "Tour" link, but the modal itself lives
 * in the persistent root layout so it survives navigation. Module-level
 * Svelte 5 rune state shares that across the unrelated component trees — the
 * same pattern as annotationStack.svelte.ts and asidePanel.svelte.ts.
 *
 * `startFirstTime()` is the automatic trigger: it only opens the tour on a
 * reader's first title-page arrival and never on mobile (no sidebar there, and the
 * clips show the desktop UI). `start()` is the explicit replay and always opens.
 * Closing the tour by any route (skip, Esc, finish) records it as seen.
 *
 * Upstream dependency: none (consumed by ReadingTour.svelte, +layout.svelte and
 * routes/+page.svelte).
 */

// Bumping this key re-shows the tour to everyone (e.g. after the steps change
// materially).
const STORAGE_KEY = 'digital-paper-tour-seen-v1';
// Matches the layout's mobile breakpoint (see +layout.svelte).
const MOBILE_QUERY = '(max-width: 719px)';

let open = $state(false);
let step = $state(0);

function hasSeen(): boolean {
	try {
		return localStorage.getItem(STORAGE_KEY) === '1';
	} catch {
		// Storage unavailable (private mode etc.): treat as seen rather than
		// risk showing the tour on every single click.
		return true;
	}
}

function markSeen() {
	try {
		localStorage.setItem(STORAGE_KEY, '1');
	} catch {
		// Storage unavailable: nothing to persist.
	}
}

export const tour = {
	get open() {
		return open;
	},
	get step() {
		return step;
	},
	/** Open the tour at the first step, unconditionally (the replay link). */
	start() {
		step = 0;
		open = true;
	},
	/** Open the tour only if this reader hasn't seen it and isn't on mobile. */
	startFirstTime() {
		if (typeof window === 'undefined') return;
		if (window.matchMedia(MOBILE_QUERY).matches || hasSeen()) return;
		this.start();
	},
	/** Move to step `i`; callers clamp to the step count they render. */
	goTo(i: number) {
		step = i;
	},
	close() {
		open = false;
		markSeen();
	}
};
