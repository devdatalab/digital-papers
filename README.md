# Open Scientific Papers for the AI Age

This repo lets you build a beautiful, open digital publication based on [our demonstration project](https://nobel-prizes.devdatalab.org) on open scientific papers.

What should an open scientific paper look like?

- You can explore results dynamically
- You can dig deeper into any part of the methods, including the intermediate steps
- You have visibility on many of the authors' intermediate analyses
- You can explore the raw data—from your browser
- You can replicate and remix it with a one-shot AI prompt



See [our demonstration project](https://nobel-prizes.devdatalab.org) and [our X thread](https://en.rattibha.com/thread/2108204197921620159) about it. 

<img src="/Users/f0018fb/Library/Application Support/typora-user-images/image-20261014155236896.png" alt="image-20261014155236896" style="zoom:33%;" />



## How to use this repo — it's EASY

1. Clone the repo
2. Give a local agent access to (i) this repo; (ii) the code repo for your project; (iii) your paper (ideally in .tex source but whatever)
3. Tell the agent to build a prototype digital publication for your paper
4. Iterate with prompts until you have exactly what you want



That's all you need. Everything else below is written by agents and for agents. Curious humans should probably just ask an agent their questions instead of reading the slop below.



## What's in this repo

This starter includes a small fictional paper, a curated Nobel teaching example,
and a new-paper template. Clone it, make it your own, and keep the examples nearby as long as they are useful.

### Requirements

We used Node.js 22.12 and Python 3.11.

```sh
npm ci
npm run dev                 # small fictional example
npm run dev:nobel           # Nobel feature showcase
npm run dev:paper           # your starting template
```

Stop the current dev server before switching papers. Each command selects the
paper at startup. The terminal prints the local address. Ask your agent to change
files in the active paper folder; both examples remain available for reference.

```sh
npm run build               # minimal → build/
npm run build:nobel         # Nobel → build/
npm run build:paper         # your paper → build/
npm run preview             # preview the last build; select the same paper if needed
npm run check
npm run check:nobel
npm run reproduce           # fictional exhibits: standard-library Python
npm run reproduce:nobel     # Nobel: install its reproduction requirements first
npm run verify              # source fidelity, registrations, public-file audit
```

For another paper folder: `npm run dev -- --paper papers/another-paper`.
Use the same `--paper` option with build, check and preview. Build output is replaced
when switching papers; generated assets and archives are ignored by Git.

## Adapt your papers

Open this repo in Codex or another local coding agent and use:

> Read AGENTS.md and docs/adapt-a-paper.md. My manuscript, bibliography and figure
> code are at [project path]. Build my digital paper in papers/my-paper. Preserve
> text, equations, citations, captions, notes and results exactly unless I request
> an edit. Reuse the analysis code or rebuild it in Python. Every displayed scientific
> exhibit must be reproducible. Refer to the examples for presentation ideas, and
> report source conflicts or anything you cannot reproduce faithfully.

See [the adaptation guide](docs/adapt-a-paper.md) and
[the feature index](docs/features.md). Start with the source paper's existing figures;
add interactive treatments as the author requests them.

## Structure

- `src/routes/` and `src/lib/reading/`: one shared static Svelte application.
- `examples/minimal/`: short fictional paper and synthetic data.
- `examples/nobel/`: selected original content, full chart inputs, and explorer examples.
- `papers/my-paper/`: editable starting template.
- Each paper: `paper.config.ts`, `content/`, `exhibits/`, `assets/`, `reproduction/`.
- `scripts/`: local paper selection, asset preparation and verification.

`content/` stores JSON; `exhibits/index.ts` registers the cover, figure/table renderers,
sidebar exhibits and optional explorer pages. `paper.config.ts` controls the footer
credit, branding, site URL, tour and extra navigation. Your agent can change these
without duplicating the reading shell. New scientific charts belong in the paper folder.
Shared chart primitives and theme tokens come from `@devdatalab/ddl-charts`.

## Nobel example

The teaching excerpt preserves retained source wording and exhibit notes, marks
omissions, and replaces submission history with permission-reminder placeholders.
The raw explorer displays five rows; chart calculations use the complete inputs.
Instructional introductions are labeled. This example is independent of the complete
publication at [nobel-prizes.devdatalab.org](https://nobel-prizes.devdatalab.org/).
The official site demonstrates additional ideas; this starter never fetches its content.

## Publish and reuse

Run locally first. [Hosting instructions](docs/hosting.md) cover GitHub Pages and
Netlify, plus an optional manual deployment of the minimal example. No deployment
runs automatically on push.

Framework software is MIT; the supplied starter design, instructions and fictional
examples are CC0. **Real paper text, figures, tables, captions, notes and paper-specific
explanations are excluded from both grants**, including papers you add to this repo.
Research data, imported analysis code and third-party material retain separate terms.
Before posting a paper, check the journal agreement and sharing policy for that version;
using this starter does not grant permission to host or relicense it.
Read [the licensing scope](COPYRIGHT.md).
