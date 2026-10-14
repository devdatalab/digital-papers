/**
 * Full-text search over the paper's sections.
 *
 * Why this file exists:
 *   Powers the header search box (`SearchBox.svelte`). It flattens every
 *   section's JSON (prose, headings, figure/table captions, collapsible panels,
 *   FAQ questions and answers, footnotes) into one record per block, each
 *   carrying the DOM id that `SectionBody` gives that block. A hit can then
 *   navigate to `/{section}#{anchor}` and highlight the exact block.
 *
 *   The corpus is small (six sections, roughly a hundred blocks), so the index is
 *   built in the browser on first use rather than shipped as a prebuilt file.
 *   That keeps dev and production identical and means there is no build step
 *   to forget. MiniSearch is loaded with a dynamic import, so readers who never
 *   search don't pay for it.
 *
 * Upstream dependencies: `minisearch` (npm), section content and `manifest`
 * from $lib/content, and `inlineText` / `blockAnchor` from $lib/content/text
 * (shared with SectionBody so excerpts and anchors match the rendered page).
 */

import type MiniSearch from 'minisearch';
import type { SearchResult as MiniSearchResult } from 'minisearch';
import { manifest, getSection, type Block, type Section } from '$lib/content';
import { inlineText, blockAnchor } from '$lib/content/text';

/** What kind of block a hit came from; drives the label shown in results. */
export type RecordKind =
	| 'paragraph'
	| 'heading'
	| 'epigraph'
	| 'figure'
	| 'table'
	| 'collapsible'
	| 'faq'
	| 'footnote';

export interface SearchRecord {
	/** Unique across the site: `{sectionId}#{anchor}`. */
	id: string;
	sectionId: string;
	/** e.g. "3. Results", shown as the hit's location. */
	sectionLabel: string;
	/** DOM id of the target element on the section page. */
	anchor: string;
	kind: RecordKind;
	/** Short context label (e.g. "Figure 2", "Note 4", the enclosing panel's
	 *  title). Indexed with a boost, so searching "figure 2" finds the figure. */
	label: string;
	text: string;
}

export interface SearchHit {
	record: SearchRecord;
	/** Lower-cased document terms that matched, for excerpt highlighting. */
	terms: string[];
}

function collectBlocks(
	section: Section,
	sectionLabel: string,
	blocks: Block[],
	path: number[],
	context: string,
	out: SearchRecord[]
) {
	const push = (kind: RecordKind, anchor: string, label: string, text: string) => {
		if (!text.trim()) return;
		out.push({ id: `${section.id}#${anchor}`, sectionId: section.id, sectionLabel, anchor, kind, label, text });
	};

	blocks.forEach((block, i) => {
		const blockPath = [...path, i];
		const anchor = blockAnchor(blockPath);
		switch (block.type) {
			case 'paragraph':
				push('paragraph', anchor, context, inlineText(block.nodes));
				break;
			case 'heading':
				push('heading', anchor, block.number, block.text);
				break;
			case 'epigraph':
				push('epigraph', anchor, block.attribution, block.text);
				break;
			case 'figure':
			case 'table': {
				const name = block.type === 'figure' ? 'Figure' : 'Table';
				// Must match SectionBody: labelled floats keep their `ref-` id.
				const target = block.label ? `ref-${block.label}` : anchor;
				push(block.type, target, block.number ? `${name} ${block.number}` : name, block.caption ?? '');
				break;
			}
			case 'collapsible':
				push('collapsible', anchor, 'Panel', block.title);
				collectBlocks(section, sectionLabel, block.blocks, blockPath, block.title, out);
				break;
			case 'faq':
				block.items.forEach((item, j) => {
					push('faq', item.id, `Q${j + 1}`, item.question);
					collectBlocks(section, sectionLabel, item.blocks, [...blockPath, j], `Q${j + 1}`, out);
				});
				break;
			// 'links' blocks are lists of outbound URLs, not prose; skip them.
		}
	});
}

/** Every searchable block across all sections, in reading order. */
export function buildRecords(): SearchRecord[] {
	const out: SearchRecord[] = [];
	for (const entry of manifest) {
		const section = getSection(entry.id);
		if (!section) continue;
		const sectionLabel = `${section.number}. ${section.title}`;
		collectBlocks(section, sectionLabel, section.blocks, [], '', out);
		section.footnotes.forEach((note, i) => {
			const text = inlineText(note.nodes);
			if (!text) return;
			out.push({
				id: `${section.id}#${note.id}`,
				sectionId: section.id,
				sectionLabel,
				anchor: note.id,
				kind: 'footnote',
				label: `Note ${i + 1}`,
				text
			});
		});
	}
	return out;
}

/** Fold case and accents so "schrodinger" finds "Schrödinger". */
function normalize(term: string): string {
	return term.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase();
}

// Dropped from both the index and queries. Without this, the any-word
// fallback lets "the" or "of" match nearly every block and drown the one
// informative word in a query.
const STOP_WORDS = new Set(
	'a an and are as at be by for from has have in is it its of on or that the their this to was were which with'.split(
		' '
	)
);

let indexPromise: Promise<MiniSearch<SearchRecord>> | null = null;

/** Build (once) and return the index. Safe to call repeatedly; call it early
 *  (e.g. on input focus) to hide the build behind the reader's typing. */
export function loadIndex(): Promise<MiniSearch<SearchRecord>> {
	indexPromise ??= import('minisearch')
		.then(({ default: MiniSearchCtor }) => {
			const index = new MiniSearchCtor<SearchRecord>({
				fields: ['text', 'label'],
				storeFields: ['sectionId', 'sectionLabel', 'anchor', 'kind', 'label', 'text'],
				processTerm: (term) => {
					const t = normalize(term);
					return t && !STOP_WORDS.has(t) ? t : null;
				},
				searchOptions: {
					boost: { label: 2 },
					// Prefix-match only the word still being typed (the last one),
					// and not a lone character: otherwise "figure 2" also matches
					// "2017", "2019", ...
					prefix: (term, i, terms) => i === terms.length - 1 && term.length > 1,
					// Allow roughly one typo per five characters, but never on
					// very short terms, where fuzziness mostly adds noise.
					fuzzy: (term) => (term.length > 4 ? 0.2 : false)
				}
			});
			index.addAll(buildRecords());
			return index;
		})
		.catch((err) => {
			// Let the next focus retry instead of caching a failure forever
			// (e.g. the chunk failed to load on a flaky connection).
			indexPromise = null;
			throw err;
		});
	return indexPromise;
}

function toHit(result: MiniSearchResult): SearchHit {
	const { id, sectionId, sectionLabel, anchor, kind, label, text } = result;
	return { record: { id, sectionId, sectionLabel, anchor, kind, label, text }, terms: result.terms };
}

/** Search the index. Every query word must match (AND); if that finds nothing,
 *  fall back to any-word (OR) so a long query with one stray word still
 *  returns something useful. */
export async function search(query: string, limit = 20): Promise<SearchHit[]> {
	const q = query.trim();
	if (!q) return [];
	const index = await loadIndex();
	let results = index.search(q, { combineWith: 'AND' });
	if (results.length === 0) results = index.search(q, { combineWith: 'OR' });
	return results.slice(0, limit).map(toHit);
}

export interface ExcerptPart {
	text: string;
	match: boolean;
}

/** A short window of `text` around the first matched term, split into plain
 *  and matched parts so the UI can wrap matches in <mark> without {@html}. */
export function excerpt(text: string, terms: string[], radius = 70): ExcerptPart[] {
	const escaped = terms
		.filter(Boolean)
		.sort((a, b) => b.length - a.length)
		.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
	// Terms come back accent-folded, so match against a folded copy of the text.
	// NFD folding changes string length, so fold per UTF-16 unit (one char in,
	// one char out) to keep offsets aligned with the original text.
	const folded = text
		.split('')
		.map((ch) => normalize(ch).charAt(0) || ch)
		.join('');
	const re = escaped.length ? new RegExp(`(?<![\\p{L}\\p{N}])(?:${escaped.join('|')})`, 'giu') : null;

	const first = re ? re.exec(folded) : null;
	let start = 0;
	let end = text.length;
	if (text.length > radius * 2) {
		const centre = first ? first.index : 0;
		start = Math.max(0, centre - radius);
		end = Math.min(text.length, start + radius * 2);
		// Snap to word boundaries so the excerpt doesn't open mid-word.
		if (start > 0) start = text.indexOf(' ', start) + 1 || start;
		if (end < text.length) end = text.lastIndexOf(' ', end) > start ? text.lastIndexOf(' ', end) : end;
	}

	const parts: ExcerptPart[] = [];
	if (start > 0) parts.push({ text: '… ', match: false });
	let cursor = start;
	if (re) {
		re.lastIndex = start;
		let m: RegExpExecArray | null;
		while ((m = re.exec(folded)) && m.index < end) {
			if (m.index > cursor) parts.push({ text: text.slice(cursor, m.index), match: false });
			const stop = Math.min(m.index + m[0].length, end);
			parts.push({ text: text.slice(m.index, stop), match: true });
			cursor = stop;
		}
	}
	if (cursor < end) parts.push({ text: text.slice(cursor, end), match: false });
	if (end < text.length) parts.push({ text: ' …', match: false });
	return parts;
}
