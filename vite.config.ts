/** Configure one selected paper, shared SvelteKit routes, and portable static assets. */
import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import path from 'node:path';
import fs from 'node:fs';
import { preparePaper } from './scripts/prepare-paper.mjs';

const root = process.cwd();
const selected = preparePaper(root, process.env.PAPER || 'examples/minimal');
const base = (process.env.BASE_PATH ?? '') as '' | `/${string}`;

export default defineConfig({
  plugins: [sveltekit({
    compilerOptions: { runes: ({ filename }) => filename.split(/[/\\]/).includes('node_modules') ? undefined : true },
    adapter: adapter({ fallback: '404.html' }),
    paths: { base },
    prerender: {
      handleUnseenRoutes: ({ routes, message }) => {
        const referee = JSON.parse(fs.readFileSync(path.join(selected.paper, 'content/referee-submissions.json'), 'utf8'));
        if (referee.submissions.length === 0 && routes.every((route) => route === '/[section]/[submission]')) return;
        throw new Error(message);
      }
    },
    files: { assets: selected.assets },
    alias: { $paper: selected.paper, $nobel: path.join(root, 'examples/nobel') }
  })]
});
