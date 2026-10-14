/** List the selected paper's public reproduction bundle during prerendering; depends on prepared assets. */
import { readdirSync } from 'node:fs';
import { resolve, join } from 'node:path';
import type { PageServerLoad } from './$types';
function list(folder: string, prefix = ''): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry) => {
    const relative = `${prefix}${entry.name}`;
    return entry.isDirectory() ? list(join(folder, entry.name), `${relative}/`) : [relative];
  }).sort();
}
export const load: PageServerLoad = () => ({ files: list(resolve('.paper-assets/downloads/reproduction')) });
