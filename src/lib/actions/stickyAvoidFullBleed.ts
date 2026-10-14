/**
 * stickyAvoidFullBleed — Svelte action that keeps a `position: sticky` sidebar
 * from overlapping full-bleed (100vw breakout) elements as the reader scrolls.
 *
 * Why it exists: the left table of contents is pinned via `position: sticky`, but
 * full-bleed visualisations (e.g. `.viz-full`, marked with `data-full-bleed`)
 * break out of the centre column to span the viewport and thus paint across the
 * sidebar's vertical band. This action nudges the sticky element with a
 * `translateY` so its bottom edge rests on the top of an approaching full-bleed
 * element and rides upward off-screen with it, then snaps back to the pin line
 * once the element has scrolled fully past — avoiding any overlap.
 *
 * Usage: apply to the sticky wrapper, passing the current route so the target
 * cache refreshes on client-side navigation:
 *     <div class="sticky" use:stickyAvoidFullBleed={pathname}>…</div>
 *
 * Contract / dependencies:
 *   - The sticky element must resolve `position: sticky` with a px `top` offset.
 *   - Full-bleed targets are any `[data-full-bleed]` elements inside the nearest
 *     `<main data-col-main>` (see +layout.svelte). Absent that ancestor, it falls
 *     back to `document`.
 *   - Self-disables when the element's computed position is not `sticky` (the
 *     mobile static layout), clearing any applied transform.
 */
import type { Action } from 'svelte/action';

export const stickyAvoidFullBleed: Action<HTMLElement, string | undefined> = (node) => {
	const scope =
		(node.closest('.shell')?.querySelector('[data-col-main]') as HTMLElement | null) ??
		document;

	let targets: HTMLElement[] = [];
	let frame = 0;

	const refreshTargets = () => {
		targets = Array.from(scope.querySelectorAll<HTMLElement>('[data-full-bleed]'));
		update();
	};

	const update = () => {
		frame = 0;
		const styles = getComputedStyle(node);

		// On the mobile static layout the sidebar is not sticky — leave it alone.
		if (styles.position !== 'sticky') {
			node.style.transform = '';
			return;
		}

		const pin = parseFloat(styles.top) || 0; // viewport offset the element pins to
		const height = node.offsetHeight; // unaffected by transform (layout height)

		let target = pin;
		for (const el of targets) {
			const rect = el.getBoundingClientRect();
			// The full-bleed element is within the sticky element's pinned band.
			if (rect.top < pin + height && rect.bottom > pin) {
				target = Math.min(target, rect.top - height);
			}
		}

		const dy = target - pin; // always <= 0
		node.style.transform = dy < 0 ? `translateY(${dy}px)` : '';
	};

	const onScroll = () => {
		if (!frame) frame = requestAnimationFrame(update);
	};

	window.addEventListener('scroll', onScroll, { passive: true });
	window.addEventListener('resize', onScroll, { passive: true });

	// Catch full-bleed elements mounting, reflowing, or resizing after load.
	const observed = scope === document ? document.body : (scope as HTMLElement);
	const resizeObserver = new ResizeObserver(refreshTargets);
	resizeObserver.observe(observed);

	refreshTargets();

	return {
		// Refires on route change (param = pathname): re-query full-bleed targets.
		update() {
			refreshTargets();
		},
		destroy() {
			if (frame) cancelAnimationFrame(frame);
			window.removeEventListener('scroll', onScroll);
			window.removeEventListener('resize', onScroll);
			resizeObserver.disconnect();
			node.style.transform = '';
		}
	};
};
