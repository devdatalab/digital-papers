/**
 * Serialises the whole paper to a single Markdown document.
 *
 * Why this file exists:
 *   LLMs (and anyone who wants plain text) read Markdown far better than the
 *   interactive section pages. The `/paper.md` endpoint
 *   (src/routes/paper.md/+server.ts) prerenders this output to a static file,
 *   and the Replication page's copy-paste LLM prompt links to it.
 *
 *   It walks the same section JSON that `SectionBody` renders, reusing
 *   `refDisplayText` from ./text so cross-references read identically. Figures
 *   and tables are interactive components on the site, so here they appear as
 *   their caption plus a link to the page that renders them. Annotation panels
 *   (editorial asides) are linked by their reading-order ids; their bodies are
 *   omitted.
 *
 * Upstream dependencies: meta, manifest and section content from ./index,
 * `refDisplayText` from ./text.
 */

import { meta, manifest, getSection, getAnnotationLocation, type Block, type InlineNode, type ReferenceEntry } from './index';
import { refDisplayText } from './text';

/** The live site's absolute URL. Markdown and LLM prompts are read outside the
 *  app, so they can't resolve SvelteKit's relative `base`. */
import config from '$paper/paper.config';
import { base } from '$app/paths';
export const SITE_URL = config.siteUrl.replace(/\/$/, '') || base;

/** Footnote labels must be unique across the document, but footnote ids are
 *  only section-unique, so prefix them with the section number. */
function fnLabel(sectionNumber: string, index: number): string {
	return `${sectionNumber}-${index + 1}`;
}

function inline(nodes: InlineNode[], fnIndex: Map<string, string>): string {
	let out = '';
	nodes.forEach((node, i) => {
		switch (node.t) {
			case 'text':
			case 'cite':
				out += node.text;
				break;
			case 'emph':
				out += node.text.trim() ? `*${node.text.trim()}*` : node.text;
				break;
			case 'link':
				out += `[${node.text}](${node.href})`;
				break;
			case 'route':
				out += `[${node.text}](${SITE_URL}/${node.route})`;
				break;
			case 'ref':
				out += refDisplayText(node, nodes[i - 1]);
				break;
			case 'fnref': {
				const label = fnIndex.get(node.id);
				if (label) out += `[^${label}]`;
				break;
			}
			case 'annotation': {
				const sectionId = getAnnotationLocation(node.id);
				if (sectionId) out += `[${node.id}](${SITE_URL}/${sectionId}#annotation-${node.id})`;
				break;
			}
		}
	});
	return out.replace(/[ \t]+/g, ' ').trim();
}

function blocks(
	list: Block[],
	sectionId: string,
	depth: number,
	fnIndex: Map<string, string>
): string[] {
	const out: string[] = [];
	for (const block of list) {
		switch (block.type) {
			case 'paragraph': {
				const text = inline(block.nodes, fnIndex);
				if (text) out.push(text);
				break;
			}
			case 'heading':
				// Section titles are h2, so paper subsection level 2 → h3, etc.
				out.push(`${'#'.repeat(Math.min(block.level + 1, 6))} ${block.number} ${block.text}`);
				break;
			case 'epigraph':
				out.push(`> ${block.text}\n>\n> — ${block.attribution}`);
				break;
			case 'figure':
			case 'table': {
				const name = block.type === 'figure' ? 'Figure' : 'Table';
				const title = block.number ? `${name} ${block.number}` : name;
				const anchor = block.label ? `#ref-${block.label}` : '';
				out.push(
					`**${title}: ${block.caption ?? ''}** — interactive ${block.type} at ${SITE_URL}/${sectionId}${anchor}`
				);
				break;
			}
			case 'links':
				out.push(block.items.map((l) => `- [${l.label}](${l.href})`).join('\n'));
				break;
			case 'collapsible':
				out.push(`${'#'.repeat(Math.min(depth + 1, 6))} ${block.title}`);
				out.push(...blocks(block.blocks, sectionId, depth + 1, fnIndex));
				break;
			case 'faq':
				for (const item of block.items) {
					out.push(`${'#'.repeat(Math.min(depth + 1, 6))} ${item.question}`);
					out.push(...blocks(item.blocks, sectionId, depth + 1, fnIndex));
				}
				break;
		}
	}
	return out;
}

/** The full paper — front matter, every section with its footnotes, and a
 *  de-duplicated reference list — as one Markdown string. */
export function paperToMarkdown(): string {
	const parts: string[] = [
		`# ${meta.title}: ${meta.subtitle}`,
		meta.authors.map((a) => `${a.name} (${a.affiliation})`).join(', '),
		meta.date,
		`Digital edition: ${SITE_URL}/${meta.pdf ? ` · PDF: ${SITE_URL}/${meta.pdf}` : ''} · Reproduction: ${SITE_URL}/replication`,
		'## Abstract',
		meta.abstract
	];

	const references = new Map<string, ReferenceEntry>();
	for (const entry of manifest) {
		const section = getSection(entry.id);
		if (!section) continue;

		const fnIndex = new Map(section.footnotes.map((f, i) => [f.id, fnLabel(section.number, i)]));
		parts.push(`## ${section.number}. ${section.title}`);
		parts.push(...blocks(section.blocks, section.id, 2, fnIndex));
		for (const note of section.footnotes) {
			parts.push(`[^${fnIndex.get(note.id)}]: ${inline(note.nodes, fnIndex)}`);
		}
		for (const ref of section.references) references.set(ref.id, ref);
	}

	if (references.size > 0) {
		parts.push('## References');
		const sorted = [...references.values()].sort((a, b) => a.text.localeCompare(b.text));
		parts.push(sorted.map((r) => `- ${r.text}${r.url ? ` ${r.url}` : ''}`).join('\n'));
	}

	return parts.join('\n\n') + '\n';
}
