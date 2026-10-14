/** Resolve selected paper sections and registered explorer pages for static generation. */
import { error } from '@sveltejs/kit';
import { manifest, extrasEntries, getSection, getNeighbours, type Section } from '$lib/content';
import { pages } from '$paper/exhibits';
import type { EntryGenerator, PageLoad } from './$types';
export const entries: EntryGenerator = () => [...manifest, ...extrasEntries.filter((entry) => entry.id !== 'replication')].map((entry) => ({ section: entry.id }));
export const load: PageLoad = ({ params }) => {
  const extra = extrasEntries.find((entry) => entry.id === params.section);
  if (extra && pages[extra.id]) {
    const section: Section = { ...extra, blocks: [], footnotes: [], references: [] };
    return { section, prev: null, next: null, explorer: true };
  }
  const section = getSection(params.section);
  if (!section) throw error(404, `Unknown section: ${params.section}`);
  return { section, ...getNeighbours(params.section), explorer: false };
};
