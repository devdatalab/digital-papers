/**
 * Plain-text and anchor helpers shared by the block renderer and site search.
 *
 * Why this file exists:
 *   `SectionBody` renders section JSON to markup, and the search index
 *   (`$lib/search/searchIndex`) flattens the same JSON to plain text. Both need
 *   to agree on two things: what an inline node *reads as* (so a search excerpt
 *   matches what's on screen), and which DOM id each block carries (so a search
 *   hit can scroll to and highlight the exact block). Keeping those rules here
 *   means the renderer and the index can't drift apart.
 *
 * Upstream dependency: the `InlineNode` type from ./index.ts.
 */

import type { InlineNode } from './index';

// The digitized prose already spells out "Figure "/"Table "/"Section "
// immediately before the ref (carried over from LaTeX source text like
// "Figure~\ref{}"), while the ref node's own text repeats the full
// "Figure N" — so rendered naively it reads "Figure Figure N". Strip the
// repeated word here rather than editing every occurrence in content JSON.
const REF_TYPE_WORD = 'figure|table|section';
const PREV_ENDS_WITH_TYPE = new RegExp(`(?:${REF_TYPE_WORD})\\s*$`, 'i');
const LEADING_TYPE = new RegExp(`^(?:${REF_TYPE_WORD})\\s+`, 'i');

/** Display text for a `ref` node, given the node before it in the paragraph. */
export function refDisplayText(
	node: Extract<InlineNode, { t: 'ref' }>,
	prev: InlineNode | undefined
): string {
	const raw = node.text ?? node.label;
	const prevEndsWithType = prev?.t === 'text' && PREV_ENDS_WITH_TYPE.test(prev.text);
	return prevEndsWithType ? raw.replace(LEADING_TYPE, '') : raw;
}

/** The reader-visible text of a run of inline nodes. Footnote call-outs and
 *  annotation tags render as small chips, not words, so they contribute
 *  nothing. */
export function inlineText(nodes: InlineNode[]): string {
	let out = '';
	nodes.forEach((node, i) => {
		switch (node.t) {
			case 'text':
			case 'emph':
			case 'cite':
			case 'link':
			case 'route':
				out += node.text;
				break;
			case 'ref':
				out += refDisplayText(node, nodes[i - 1]);
				break;
		}
	});
	return out.replace(/\s+/g, ' ').trim();
}

/** DOM id for a block, from its index path within the section: top-level
 *  blocks are `[i]`, blocks nested in a collapsible are `[i, j]`, and FAQ
 *  answer blocks are `[faqBlock, item, j]`. Deterministic from the JSON, so the
 *  index and the rendered page always agree without storing ids in content. */
export function blockAnchor(path: number[]): string {
	return `b-${path.join('-')}`;
}
