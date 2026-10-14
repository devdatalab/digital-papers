/**
 * Prerender submissions 2–9 within the referee-response section. The first stays
 * at the existing section URL. Uses curated content and the shared section loader
 * helpers; other section slugs and invalid submission numbers remain 404s.
 */
import { error } from '@sveltejs/kit';
import { getSection, getNeighbours } from '$lib/content';
import content from '$paper/content/referee-submissions.json';
import type { EntryGenerator, PageLoad } from './$types';

const sectionId = 'referee-comments-and-responses';

export const entries: EntryGenerator = () =>
	(getSection(sectionId) ? content.submissions : []).slice(1).map((_, index) => ({ section: sectionId, submission: String(index + 2) }));

export const load: PageLoad = ({ params }) => {
	const submission = Number(params.submission);
	if (
		params.section !== sectionId ||
		!Number.isInteger(submission) ||
		String(submission) !== params.submission ||
		submission < 2 ||
		submission > content.submissions.length
	) throw error(404, 'Unknown submission');
	const section = getSection(sectionId);
	if (!section) throw error(404, 'Unknown section');
	return { section, ...getNeighbours(sectionId), submission, explorer: false };
};
