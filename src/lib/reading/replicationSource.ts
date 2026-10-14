/**
 * replicationSource — turns a replication-package source path into an in-site
 * link to the corresponding row of the "Code files" table on the Replication
 * page (`/replication`).
 *
 * Why this file exists:
 *   Figure and table footers cite the generator that produced their data (e.g.
 *   `main_spec/main_spec.py`). Those citations used to link out to the GitHub
 *   blob, but the repo is private to external readers, so the link would 404
 *   for the very audience the digital edition is for. Instead we point at the
 *   public Replication page and deep-link to the generator's row in the
 *   documented Code-files table. Every result stays traceable to its code
 *   without exposing (or requiring access to) the repository.
 *
 *   `codeAnchorId` is the single source of truth for a generator's row id, used
 *   both here (to build the `#fragment`) and by the Replication page (to stamp
 *   the `id` on each row) so the two can never drift.
 *
 * Upstream dependencies:
 *   $app/paths (base — the site is served from a repo subpath on GitHub Pages,
 *   so internal links must be prefixed with SvelteKit's `base`).
 */
import { base } from '$app/paths';

/**
 * The anchor id for a generator's row in the Replication Code-files table.
 *
 * Accepts either a full source path (`main_spec/main_spec.py`, or the
 * root-level `extract_viz_data.py`) or a bare folder (`main_spec/`), and keys
 * off the top-level generator folder so that every `.py` under a generator
 * resolves to that generator's single row.
 */
export function codeAnchorId(source: string): string {
	const folder = source
		.replace(/\/$/, '') // drop a trailing slash on bare-folder inputs
		.split('/')[0] // key off the top-level generator folder
		.replace(/\.py$/, ''); // handle root-level generators (extract_viz_data.py)
	return `code-${folder}`;
}

/**
 * The in-site URL for a source citation: the Replication page scrolled to the
 * generator's Code-files row. Respects the repo-subpath `base`.
 */
export function replicationSourceUrl(source: string): string {
	return `${base}/replication#${codeAnchorId(source)}`;
}
