/**
 * Scroll a search hit into view and briefly highlight it.
 *
 * Why this file exists:
 *   After the search box navigates to `/{section}#{anchor}`, the target block
 *   may be hidden inside a closed collapsible panel or FAQ answer, and the
 *   browser's own :target styling can't be relied on because SvelteKit
 *   navigates with pushState (which doesn't update :target). This helper does
 *   it explicitly: open any enclosing <details>, scroll the block into view,
 *   keep it there while the page settles, move focus to it, and flash it with
 *   the `.search-flash` class (styled in app.css).
 *
 *   Callers must navigate with `goto(..., { noScroll: true, keepFocus: true })`.
 *   Without `keepFocus`, SvelteKit's post-navigation focus reset runs in a
 *   setTimeout *after* this function and restores the scroll position it saved
 *   before navigating, which throws the reader back off the target.
 *
 * Upstream dependencies: the block ids rendered by SectionBody (see
 * `blockAnchor` in $lib/content/text) and the `.search-flash` rule in
 * $lib/styles/app.css.
 */

const FLASH_CLASS = 'search-flash';

// How long to hold the target in place while late layout (charts drawn on
// mount, images, web fonts) settles above it. Any reader input ends it early.
const SETTLE_MS = 1500;
const STOP_EVENTS = ['wheel', 'touchstart', 'pointerdown', 'keydown'] as const;

/** Returns false if no element with `id` is on the page. */
export function revealBlock(id: string): boolean {
	const el = document.getElementById(id);
	if (!el) return false;

	// Open every enclosing <details> (and the target itself, for a panel or FAQ
	// question hit). FaqList listens for `toggle`, so its state stays in sync.
	for (let d = el.closest('details'); d; d = d.parentElement?.closest('details') ?? null) {
		d.open = true;
	}

	// Add the class before scrolling: it also sets scroll-margin-top so a
	// 'start'-aligned block clears the sticky header. Removing and re-adding
	// (with a forced reflow between) restarts the animation on a repeat hit.
	el.classList.remove(FLASH_CLASS);
	void el.offsetWidth;
	el.classList.add(FLASH_CLASS);
	el.addEventListener('animationend', () => el.classList.remove(FLASH_CLASS), { once: true });

	// Centre short blocks; align tall ones (long panels, figures) to the top so
	// their start isn't pushed off-screen. Instant, not smooth: a smooth scroll
	// aims at where the block was when it started, so any layout shift during
	// the animation lands it in the wrong place.
	const block: ScrollLogicalPosition =
		el.getBoundingClientRect().height > window.innerHeight * 0.6 ? 'start' : 'center';
	const scroll = () => el.scrollIntoView({ behavior: 'instant', block });
	scroll();

	// Move keyboard and screen-reader focus to the hit, as a native fragment
	// jump would. tabindex -1 makes a <p> focusable without adding it to the
	// tab order; it is removed again once focus leaves.
	if (!el.hasAttribute('tabindex')) {
		el.setAttribute('tabindex', '-1');
		el.addEventListener('blur', () => el.removeAttribute('tabindex'), { once: true });
	}
	el.focus({ preventScroll: true });

	holdInPlace(el, scroll);
	return true;
}

/** For SETTLE_MS, re-scroll whenever content above `el` changes size and
 *  moves it, until the reader scrolls or clicks. */
function holdInPlace(el: HTMLElement, scroll: () => void) {
	let expected = el.getBoundingClientRect().top;
	let frame = 0;
	const deadline = performance.now() + SETTLE_MS;

	const stop = () => {
		cancelAnimationFrame(frame);
		for (const type of STOP_EVENTS) window.removeEventListener(type, stop);
	};
	for (const type of STOP_EVENTS) window.addEventListener(type, stop, { passive: true });

	const check = () => {
		if (!el.isConnected || performance.now() > deadline) return stop();
		if (Math.abs(el.getBoundingClientRect().top - expected) > 1) {
			scroll();
			expected = el.getBoundingClientRect().top;
		}
		frame = requestAnimationFrame(check);
	};
	frame = requestAnimationFrame(check);
}
