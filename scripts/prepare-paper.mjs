/** Select a local paper and stage only its assets/reproduction downloads; no Git dependency. */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
/** @param {string} root @param {string} selection */
export function preparePaper(root, selection) {
  const paper = path.resolve(root, selection);
  const relative = path.relative(root, paper);
  if (relative.startsWith('..') || path.isAbsolute(relative) || !fs.existsSync(path.join(paper, 'paper.config.ts'))) {
    throw new Error('PAPER must name a paper folder inside this checkout containing paper.config.ts');
  }
  const assets = path.join(root, '.paper-assets');
  fs.rmSync(assets, { recursive: true, force: true });
  fs.mkdirSync(assets, { recursive: true });
  if (fs.existsSync(path.join(paper, 'assets'))) fs.cpSync(path.join(paper, 'assets'), assets, { recursive: true });
  const reproduction = path.join(paper, 'reproduction');
  if (fs.existsSync(reproduction)) {
    const downloads = path.join(assets, 'downloads');
    fs.mkdirSync(downloads, { recursive: true });
    fs.cpSync(reproduction, path.join(downloads, 'reproduction'), {
      recursive: true,
      filter: (file) => !path.relative(reproduction, file).split(path.sep).some((part) => part.startsWith('.') || ['__pycache__', 'node_modules'].includes(part)) && !fs.lstatSync(file).isSymbolicLink()
    });
    const expected = path.join(downloads, 'reproduction', 'expected');
    if (fs.existsSync(path.join(paper, 'data'))) {
      fs.mkdirSync(expected, { recursive: true });
      for (const name of fs.readdirSync(path.join(paper, 'data')).filter((name) => name.endsWith('.json'))) {
        fs.copyFileSync(path.join(paper, 'data', name), path.join(expected, name));
      }
    }
    execFileSync('python3', ['-c', 'import shutil,sys; shutil.make_archive(sys.argv[1], "zip", root_dir=sys.argv[2], base_dir="reproduction")', path.join(downloads, 'reproduction'), downloads]);
  }
  return { paper, assets };
}
