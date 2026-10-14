/** Typed access to the selected paper’s JSON, references and annotation locations.
 * Depends on $paper/content; paper selection is configured in vite.config.ts. */

import manifestJson from '$paper/content/manifest.json';
import config from '$paper/paper.config';
import metaJson from '$paper/content/meta.json';

/** Inline content within a paragraph or footnote. */
export type InlineNode =
	| { t: 'text'; text: string }
	| { t: 'emph'; text: string }
	| { t: 'cite'; cmd: 'citep' | 'citet' | 'cite'; keys: string[]; refIds: string[]; text: string }
	| { t: 'ref'; label: string; text?: string }
	| { t: 'link'; href: string; text: string }
	/** Internal SvelteKit route (e.g. an Extras page). `route` is base-relative
	 *  with no leading slash (e.g. "extended-results"); the renderer prefixes
	 *  `base` and uses in-app client navigation rather than opening a new tab. */
	| { t: 'route'; route: string; text: string; small?: boolean }
	| { t: 'annotation'; id: string }
	/** A footnote call-out in the prose — the counterpart of a `Footnote` with
	 *  the same `id` in the owning section's `footnotes`. Carries no number of
	 *  its own: the reader-facing number comes from the footnote's position in
	 *  that array (see `Footnote`). */
	| { t: 'fnref'; id: string };

/** A block of rendered content within a section. */
export type Block =
	| { type: 'paragraph'; nodes: InlineNode[] }
	| { type: 'heading'; level: number; number: string; text: string }
	| { type: 'epigraph'; text: string; attribution: string }
	| { type: 'figure' | 'table'; label: string | null; number?: string; caption: string | null; source?: string | null }
	| { type: 'links'; items: { label: string; href: string }[] }
	| { type: 'collapsible'; title: string; collapsed?: boolean; small?: boolean; blocks: Block[] }
	/** A list of question/answer pairs, rendered as an accordion by `FaqList`.
	 *  Answers are ordinary blocks, so they get citations, annotation tags and
	 *  cross-references like any other prose. */
	| { type: 'faq'; items: FaqItem[] };

export interface FaqItem {
	/** Stable, page-unique anchor (e.g. "faq-q1") so a question can be deep-linked. */
	id: string;
	question: string;
	blocks: Block[];
}

export interface Footnote {
	/** Stable, section-unique handle linking this note to its `fnref` call-out.
	 *  Not the displayed number: notes are stored in document order and numbered
	 *  from their index, so the two can never disagree. (The pipeline's old
	 *  `marker` field numbered per-subsection and had gone stale — e.g. results
	 *  restarted at 1 three times — so it was dropped rather than trusted.) */
	id: string;
	nodes: InlineNode[];
}

export interface ReferenceEntry {
	id: string;
	key: string;
	text: string;
	/** Link-out to the publication itself (DOI, NBER page, JSTOR, etc.).
	 *  Omitted when no reliable source could be verified. */
	url?: string;
}

/** Content within a right-hand annotation panel — deliberately minimal (no
 *  citations/footnotes) since these are editorial asides, not paper prose.
 *  The `component` variant hosts an interactive appendix figure/table: its
 *  `component` string keys into the appendix registry (see
 *  `$paper/exhibits`), and `props` are forwarded to it. */
export type AnnotationBlock =
	| { type: 'paragraph'; text: string; nodes?: { t: 'text' | 'emph'; text: string }[] }
	| { type: 'image'; src: string; alt: string; caption?: string }
	| { type: 'component'; component: string; props?: Record<string, unknown> };

export interface AnnotationEntry {
	id: string;
	title: string;
	subtitle: string;
	body: AnnotationBlock[];
}

export interface Section {
	id: string;
	number: string;
	title: string;
	/** The section's label in the source manuscript (e.g. "sec:methods"), when
	 *  prose elsewhere cross-references it. Lets a `ref` inline node resolve to
	 *  this section the same way figure/table labels resolve to their blocks —
	 *  see `getSectionTarget`. Optional: most sections are never cross-referenced
	 *  by label and carry none. */
	label?: string;
	blocks: Block[];
	footnotes: Footnote[];
	references: ReferenceEntry[];
	annotations?: AnnotationEntry[];
}

export interface ManifestEntry {
	id: string;
	number: string;
	title: string;
}

export interface Author {
	name: string;
	affiliation: string;
}

export interface Meta {
	title: string;
	subtitle: string;
	date: string;
	authors: Author[];
	abstract: string;
	/** PDF path relative to the site base (prefix with `base` when linking). */
	pdf: string;
}

export const meta: Meta = metaJson;
export const manifest: ManifestEntry[] = manifestJson;

/** Bespoke, interactive routes (not JSON-driven paper sections) grouped under an
 *  "Explore further" heading in the left nav. They are deliberately kept OUT of `manifest`
 *  so they don't feed the `[section]` prerender/loader — that route resolves
 *  slugs to section JSON via `getSection`, which has no entry for them. Unlike the
 *  numbered paper sections, Extras items carry no `number`: the TOC renders them
 *  as an unnumbered list under the group label. `manifest` remains the pure list
 *  of digitised paper sections. */
export const navEntries: ManifestEntry[] = [...manifest];
export const extrasEntries: ManifestEntry[] = config.extras;

// Eagerly load every section file so lookups are synchronous (the site is fully
// prerendered, so there is no runtime cost to bundling all sections).
const sectionModules = import.meta.glob<Section>('$paper/content/sections/*.json', {
	eager: true,
	import: 'default'
});

const sectionsById = new Map<string, Section>();
for (const mod of Object.values(sectionModules)) {
	sectionsById.set(mod.id, mod);
}

// Follow the reading order when indexing the first occurrence of a panel.
const readingSections = manifest
	.map((entry) => sectionsById.get(entry.id))
	.filter((section): section is Section => section !== undefined);

/** Look up a single section by its slug id, or undefined if unknown. */
export function getSection(id: string): Section | undefined {
	return sectionsById.get(id);
}

const annotationsById = new Map<string, AnnotationEntry>();
for (const mod of Object.values(sectionModules)) {
	for (const entry of mod.annotations ?? []) {
		annotationsById.set(entry.id, entry);
	}
}

/** Look up an annotation panel's content by its tag id (e.g. "A1"), across
 *  all sections — the tools panel stack is global, not section-scoped. */
export function getAnnotation(id: string): AnnotationEntry | undefined {
	return annotationsById.get(id);
}

export interface FigureOrTableTarget {
	sectionId: string;
	type: 'figure' | 'table';
	number: string;
}

/** Every figure/table block's label, across all sections, mapped to where it
 *  lives — lets `ref` inline nodes resolve a clickable, scroll-to-able target
 *  regardless of which section cites it. Labels with no matching block (e.g.
 *  refs to appendix figures/tables not included in this digital edition)
 *  simply have no entry. */
const figureTargetsByLabel = new Map<string, FigureOrTableTarget>();
function indexFigureTargets(sectionId: string, blocks: Block[]) {
	for (const block of blocks) {
		if ((block.type === 'figure' || block.type === 'table') && block.label && block.number) {
			figureTargetsByLabel.set(block.label, { sectionId, type: block.type, number: block.number });
		} else if (block.type === 'collapsible') {
			indexFigureTargets(sectionId, block.blocks);
		} else if (block.type === 'faq') {
			for (const item of block.items) indexFigureTargets(sectionId, item.blocks);
		}
	}
}
for (const mod of Object.values(sectionModules)) {
	indexFigureTargets(mod.id, mod.blocks);
}

/** Look up a figure/table's section and number by its label, for rendering
 *  cross-references (`ref` inline nodes) as scroll-to-able links. */
export function getFigureOrTableTarget(label: string): FigureOrTableTarget | undefined {
	return figureTargetsByLabel.get(label);
}

/** Every section's manuscript `label`, mapped to its slug — the section-level
 *  counterpart of `figureTargetsByLabel`. Prose cross-references a section by
 *  the same `ref` node it uses for floats (e.g. "Section~\ref{sec:methods}"),
 *  so the renderer needs both lookups to resolve one. Sections without a
 *  `label` (the common case) simply have no entry, and such refs degrade to
 *  unlinked text exactly as unresolvable float refs do. */
const sectionIdsByLabel = new Map<string, string>();
for (const mod of Object.values(sectionModules)) {
	if (mod.label) sectionIdsByLabel.set(mod.label, mod.id);
}

/** Look up a section's slug by its manuscript label, for rendering section
 *  cross-references (`ref` inline nodes) as links. */
export function getSectionTarget(label: string): string | undefined {
	return sectionIdsByLabel.get(label);
}

/** Every annotation id's FIRST inline occurrence, across all sections, mapped
 *  to the section slug that contains its `{ t: 'annotation' }` tag — lets an
 *  open panel offer a "Show in text" jump back to where the annotation is
 *  referenced. Tags are indexed wherever `SectionBody` renders inline nodes:
 *  prose blocks (including nested `collapsible` ones) AND the footnotes behind
 *  the "Notes" list, which is where most of the `results` annotations are
 *  actually tagged. Body blocks are walked before footnotes so an annotation
 *  tagged in both jumps to the prose tag rather than the note at the foot of
 *  the page. Annotations that are DEFINED (in `section.annotations`) but never
 *  tagged anywhere get no entry, so their jump control is simply omitted.
 *  Mirrors `figureTargetsByLabel` / `getFigureOrTableTarget`. */
const annotationLocationById = new Map<string, string>();
function indexAnnotationNodes(sectionId: string, nodes: InlineNode[]) {
	for (const node of nodes) {
		if (node.t === 'annotation' && !annotationLocationById.has(node.id)) {
			annotationLocationById.set(node.id, sectionId);
		}
	}
}
function indexAnnotationLocations(sectionId: string, blocks: Block[]) {
	for (const block of blocks) {
		if (block.type === 'paragraph') {
			indexAnnotationNodes(sectionId, block.nodes);
		} else if (block.type === 'collapsible') {
			indexAnnotationLocations(sectionId, block.blocks);
		} else if (block.type === 'faq') {
			for (const item of block.items) indexAnnotationLocations(sectionId, item.blocks);
		}
	}
}
for (const mod of readingSections) {
	indexAnnotationLocations(mod.id, mod.blocks);
	for (const note of mod.footnotes ?? []) {
		indexAnnotationNodes(mod.id, note.nodes);
	}
}

/** Look up the section slug that contains an annotation's inline tag, or
 *  undefined when the annotation is defined but never referenced in prose. */
export function getAnnotationLocation(id: string): string | undefined {
	return annotationLocationById.get(id);
}

/** Every section's list of annotation ids REFERENCED in its prose (blocks —
 *  including nested `collapsible` ones — and footnotes), in first-appearance
 *  order, de-duplicated. A section often references panels DEFINED in another
 *  section (e.g. Data & Methods badges the robustness panel A2,
 *  which `results` defines); `section.annotations` alone therefore under-counts
 *  what a page actually surfaces. `AsidePageIndex` unions this with the defined
 *  set so the "On this page" list covers every panel the reader can open here,
 *  regardless of which file owns the definition. */
const annotationRefsBySection = new Map<string, string[]>();
function collectAnnotationRefs(ids: string[], seen: Set<string>, nodes: InlineNode[]) {
	for (const node of nodes) {
		if (node.t === 'annotation' && !seen.has(node.id)) {
			seen.add(node.id);
			ids.push(node.id);
		}
	}
}
function collectAnnotationRefsFromBlocks(ids: string[], seen: Set<string>, blocks: Block[]) {
	for (const block of blocks) {
		if (block.type === 'paragraph') {
			collectAnnotationRefs(ids, seen, block.nodes);
		} else if (block.type === 'collapsible') {
			collectAnnotationRefsFromBlocks(ids, seen, block.blocks);
		} else if (block.type === 'faq') {
			for (const item of block.items) collectAnnotationRefsFromBlocks(ids, seen, item.blocks);
		}
	}
}
for (const mod of Object.values(sectionModules)) {
	const ids: string[] = [];
	const seen = new Set<string>();
	collectAnnotationRefsFromBlocks(ids, seen, mod.blocks);
	for (const note of mod.footnotes ?? []) {
		collectAnnotationRefs(ids, seen, note.nodes);
	}
	annotationRefsBySection.set(mod.id, ids);
}

/** Look up the annotation ids referenced in a section's prose, in
 *  first-appearance order. Returns an empty array for unknown sections. */
export function getReferencedAnnotationIds(sectionId: string): string[] {
	return annotationRefsBySection.get(sectionId) ?? [];
}

/** Manifest entry plus its position, for prev/next navigation. */
export function getNeighbours(id: string): {
	prev: ManifestEntry | null;
	next: ManifestEntry | null;
} {
	const i = manifest.findIndex((s) => s.id === id);
	return {
		prev: i > 0 ? manifest[i - 1] : null,
		next: i >= 0 && i < manifest.length - 1 ? manifest[i + 1] : null
	};
}
