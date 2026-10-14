/**
 * brandChrome — a Svelte context flag marking "this viz is rendering inside the
 * right-hand Additional Information pane, so drop the DDL brand wrapper".
 *
 * Why this file exists:
 *   Appendix panes show the figure/table itself, not a branded standalone
 *   artefact: the pane already has its own card chrome and heading, so a second
 *   bordered container plus a DDL logo around every item is redundant framing.
 *   Charts there render "bare" — title, subtitle, source and notes are kept, but
 *   the container border/background/padding and the logo mark are dropped.
 *
 *   A context (rather than a prop) because three of the appendix components are
 *   *also* used outside the pane, where branding must stay: FigureBinscatterRanks
 *   and FigurePermTest render in the main text via SectionBody, and
 *   OccupationRankChart renders full-size on the /occupation-rank-explorer page.
 *   AnnotationPanel is the single seam every appendix item passes through, so it
 *   sets the flag once and each viz reads it — no prop plumbing through the
 *   content JSON, and no overloading the existing `compact` prop, which is about
 *   size, not branding.
 *
 *   Consumers are BrandedFrame (declarative chrome) and the Figure* components
 *   (imperative ddl-charts `createChartContainer`, via its `showBranding`
 *   option + the `ddl-bare` class). The shared bare styling lives in
 *   `$lib/styles/app.css` under `.ddl-branded-container.ddl-bare`.
 *
 * Upstream dependencies: svelte (getContext/setContext)
 */
import { getContext, setContext } from 'svelte';

const KEY = Symbol('ddl-bare-chrome');

/** Mark this subtree as bare — call during component init (AnnotationPanel). */
export function setBareChrome() {
	setContext(KEY, true);
}

/**
 * True when the calling component renders inside a bare-chrome subtree.
 * Call during component init. Defaults to false (branded) everywhere else.
 */
export function useBareChrome(): boolean {
	return getContext<boolean>(KEY) ?? false;
}

/** Class name applied to a `.ddl-branded-container` to strip the brand wrapper. */
export const BARE_CLASS = 'ddl-bare';
