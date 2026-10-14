<!-- Agent workflow for adapting this starter; depends on README and docs/adapt-a-paper.md. -->
# Digital Papers

This is a cloneable starter for a researcher working with a local coding agent.
One shared SvelteKit application renders the selected paper. Read README.md for
commands. When creating a paper or revising its manuscript-derived content, read
[docs/adapt-a-paper.md](docs/adapt-a-paper.md) before editing.

## Source fidelity

Preserve manuscript prose, equations, citations, results, captions, table notes,
and figure notes exactly unless the user explicitly requests a substantive edit.
Change presentation freely within the task. Place optional new explanations in
separate editorial asides. Flag source-version conflicts and numerical discrepancies
for the author; never silently resolve them or invent missing scientific content.

## Where to work

Copy `examples/nobel/` into `papers/<paper-name>/` and adapt it for the author's paper.
Keep the Nobel example available for reference throughout development. The official Nobel
publication is independent; links to it are examples, not dependencies.
Read only the research inputs designated by the user, and edit external research
repositories only with explicit authorization. Keep local paths and credentials
out of public content and reproduction bundles.

## Exhibits and reproduction

Reuse the research project's analysis code, or rebuild its calculations in Python.
Every displayed scientific exhibit needs its required inputs, generating code,
provenance, and a working check in the paper's reproduction bundle. Preserve original
captions and notes. Record manually transcribed published results as manual inputs;
a copy check is not evidence that the estimates were independently recomputed.

## Implementation

Use shared reading modules in `src/lib/reading/`; keep paper content, scientific
exhibits and data in the selected paper folder. Register exhibits in `exhibits/index.ts`.
Use ddl-charts tokens and primitives; recommend reusable chart capabilities upstream.
Use SvelteKit `base` for internal routes/assets. All output must support static hosting.
Every new code file starts with a comment explaining purpose and dependencies.

After edits run the applicable Svelte check, static build and reproduction check.
Ask before adding unit tests. Run browser automation only when explicitly requested;
the author runs the dev server for visual review. Keep the Nobel example functional.
Commit, push, publish, or modify remote repositories only when authorized by the user.
