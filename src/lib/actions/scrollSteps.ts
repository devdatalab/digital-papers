/**
 * scrollSteps — Svelte action that reports which scrollytelling step is active.
 *
 * Why it exists: the title page walks the reader through the feature chart in
 * scroll-driven steps (LandingScrolly.svelte). Each step is a `[data-step]`
 * child of the node this action is applied to; a step becomes active when it
 * crosses a horizontal trigger line (by default the vertical middle of the
 * viewport). An IntersectionObserver does the work, so there is no scroll
 * listener and no layout thrash. It is small enough that pulling in scrollama
 * wasn't worth a dependency.
 *
 * Reports -1 when the reader has scrolled back above the first step (so the
 * page can return to its pre-chart state) and holds the last step once the
 * reader scrolls past the end.
 *
 * Usage:
 *     <div use:scrollSteps={{ onStep: (i) => (active = i) }}>
 *       <div data-step>…</div> <div data-step>…</div>
 *     </div>
 *
 * Candidate for ddl-charts: this is framework-agnostic apart from the Action
 * wrapper, and any future scrolly chart would want it.
 *
 * Upstream dependencies: none (browser IntersectionObserver only; actions run
 * client-side, so this is safe under adapter-static prerendering).
 */
import type { Action } from 'svelte/action';

export interface ScrollStepsOptions {
	onStep: (index: number) => void;
	/** Trigger line as a fraction of viewport height from the top (default 0.5). */
	offset?: number;
}

export const scrollSteps: Action<HTMLElement, ScrollStepsOptions> = (node, options) => {
	let opts = options;
	let current = -2; // sentinel so the first real report always fires
	let observer: IntersectionObserver | null = null;

	function report(i: number) {
		if (i === current) return;
		current = i;
		opts.onStep(i);
	}

	function connect() {
		observer?.disconnect();
		const steps = Array.from(node.querySelectorAll<HTMLElement>('[data-step]'));
		const offset = opts.offset ?? 0.5;
		// Shrink the root to a 0px line at `offset`: a step "intersects" exactly
		// while it straddles that line.
		const top = -Math.round(offset * 100);
		const bottom = -Math.round((1 - offset) * 100);
		observer = new IntersectionObserver(
			(entries) => {
				for (const entry of entries) {
					const i = steps.indexOf(entry.target as HTMLElement);
					if (entry.isIntersecting) {
						report(i);
					} else if (i === 0 && entry.boundingClientRect.top > 0) {
						// First step dropped below the line: reader went back up.
						report(-1);
					}
				}
			},
			{ rootMargin: `${top}% 0px ${bottom}% 0px`, threshold: 0 }
		);
		for (const s of steps) observer.observe(s);
	}

	connect();

	return {
		update(next) {
			opts = next;
		},
		destroy() {
			observer?.disconnect();
		}
	};
};
