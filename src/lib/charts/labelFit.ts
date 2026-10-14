/**
 * labelFit — accurate text measurement for SVG chart labels, backed by
 * `@chenglou/pretext`.
 *
 * Why this file exists:
 *   SVG `<text>` has no native wrapping or width query, so our D3 figures have
 *   historically reserved a magic-number left gutter (`margin.left`) and
 *   truncated category labels by *character count* (e.g. `slice(0, 21) + '…'`).
 *   That over-reserves space for short labels and clips labels that would
 *   actually fit. pretext measures real pixel widths against the browser font
 *   engine (via a one-time canvas pass, then pure arithmetic — no DOM reflow),
 *   letting us size gutters to the true widest label and truncate at the real
 *   pixel boundary.
 *
 * Browser-only: pretext measures through a canvas 2D context, so every function
 * here must run client-side (our figures already build in `onMount`), never
 * during SSR/prerender.
 *
 * Upstream dependencies:
 *   @chenglou/pretext (prepareWithSegments, measureNaturalWidth)
 *
 * Note: this is a generic SVG-charting concern, not specific to this paper. If
 * we keep leaning on it, it's a good candidate to upstream into
 * `@devdatalab/ddl-charts` as a shared primitive rather than living here.
 */
import { prepareWithSegments, measureNaturalWidth } from '@chenglou/pretext';

/**
 * Build a canvas `font` shorthand (what pretext expects) from an element's
 * computed font-family plus an explicit pixel size. Our SVG labels set their
 * own `font-size` but inherit `font-family` from the page, so we read the
 * family off a real rendered node to measure exactly what the browser paints.
 *
 * @param el      a mounted element whose computed font-family matches the labels
 * @param sizePx  the label font-size in px (as set on the `<text>` elements)
 * @param weight  optional font-weight (omit for normal/400)
 */
export function resolveCanvasFont(el: Element, sizePx: number, weight?: number | string): string {
	const family = getComputedStyle(el).fontFamily || 'sans-serif';
	return weight != null ? `${weight} ${sizePx}px ${family}` : `${sizePx}px ${family}`;
}

/** Natural single-line pixel width of `text` rendered in `font`. */
export function measureLabelWidth(text: string, font: string): number {
	return measureNaturalWidth(prepareWithSegments(text, font));
}

/** Widest natural label width across `labels`, in pixels (0 for an empty list). */
export function maxLabelWidth(labels: readonly string[], font: string): number {
	let max = 0;
	for (const label of labels) {
		const w = measureLabelWidth(label, font);
		if (w > max) max = w;
	}
	return max;
}

/**
 * Truncate `label` to fit within `maxPx`, appending `ellipsis` only when the
 * full label does not fit. Returns the longest code-point prefix whose measured
 * width (including the ellipsis) is within `maxPx`. Unlike a character-count
 * cutoff, this reflects real glyph widths, so wide and narrow labels each get as
 * much text as actually fits.
 *
 * Code points (via `Array.from`) rather than UTF-16 units, so surrogate pairs /
 * combined emoji are never split mid-glyph.
 */
export function fitLabel(label: string, maxPx: number, font: string, ellipsis = '…'): string {
	if (maxPx <= 0) return '';
	if (measureLabelWidth(label, font) <= maxPx) return label;

	const chars = Array.from(label);
	// Largest prefix length `k` such that (prefix + ellipsis) still fits.
	let lo = 0;
	let hi = chars.length;
	let best = 0;
	while (lo <= hi) {
		const mid = (lo + hi) >> 1;
		const candidate = chars.slice(0, mid).join('').trimEnd() + ellipsis;
		if (measureLabelWidth(candidate, font) <= maxPx) {
			best = mid;
			lo = mid + 1;
		} else {
			hi = mid - 1;
		}
	}
	if (best <= 0) return ellipsis; // even one char + ellipsis overflows
	return chars.slice(0, best).join('').trimEnd() + ellipsis;
}
