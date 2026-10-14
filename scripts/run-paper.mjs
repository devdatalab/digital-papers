/** Run the shared application for a selected paper; depends on Vite and paper.config.ts. */
import { spawnSync } from 'node:child_process';
const [command = 'dev', ...args] = process.argv.slice(2);
const flag = args.indexOf('--paper');
const paper = flag < 0 ? (process.env.PAPER || 'examples/minimal') : args.splice(flag, 2)[1];
if (!['dev', 'build', 'preview', 'check'].includes(command)) throw new Error('Expected dev, build, preview or check');
const bin = command === 'check' ? 'svelte-check' : 'vite';
const options = command === 'check' ? ['--tsconfig', './tsconfig.json', ...args] : [command, ...args];
if (command === 'check') {
  const sync = spawnSync('node_modules/.bin/svelte-kit', ['sync'], { stdio: 'inherit', env: { ...process.env, PAPER: paper } });
  if (sync.status) process.exit(sync.status);
}
const result = spawnSync(`node_modules/.bin/${bin}`, options, { stdio: 'inherit', env: { ...process.env, PAPER: paper } });
process.exit(result.status ?? 1);
