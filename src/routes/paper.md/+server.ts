/**
 * Serves the whole paper as Markdown at `{base}/paper.md`.
 *
 * Why this file exists: a plain-text copy of the paper that LLMs can ingest
 * directly (it is linked from the Replication page's AI prompt). There is no
 * UI for it. Prerendered like the rest of the site, so the static build emits
 * a real `paper.md` file (GitHub Pages serves it as-is; static/.nojekyll stops
 * Jekyll from turning it into HTML).
 *
 * Upstream dependency: `paperToMarkdown` from $lib/content/markdown.
 */

import { paperToMarkdown } from '$lib/content/markdown';

export const prerender = true;

export function GET() {
	return new Response(paperToMarkdown(), {
		headers: { 'content-type': 'text/markdown; charset=utf-8' }
	});
}
