<!-- Ordered adaptation workflow for a local agent; depends on AGENTS.md and paper folders. -->
# Adapt a paper

## 1. Establish the sources

Read the user-designated manuscript, bibliography, figure/table assets and analysis
code. Record the selected draft's version and the source of each exhibit. If versions
conflict, ask the author which is authoritative. Keep private project paths in local,
ignored notes, rather than public content. Read only inputs the user designates.

Completion: every proposed section and exhibit has an identified source; unresolved
inputs are listed explicitly. A PDF can be a reference, but never invent omitted text.

## 2. Create the paper

Use `papers/my-paper/` or copy `examples/minimal/` into another `papers/` folder.
Set metadata and navigation, then replace the fictional content. Keep both examples
as references. There is no importer; the agent performs the conversion and verifies it.

Preserve original prose, equations, citation identity, captions and notes exactly.
The inline model includes text, emphasis, citations, internal routes, cross-references,
footnotes and annotation tags. Blocks include prose, headings, exhibits, collapsibles,
and FAQ lists. For richer math or formatting, extend the renderer explicitly; do not
flatten unsupported source material into approximate prose.

Completion: all imported scientific content has been compared with the authoritative
source. Every footnote, citation and cross-reference resolves; unsupported material
is identified to the author rather than silently discarded.

## 3. Add the exhibits

Initially reuse existing figure assets where useful: a figure/table block can name
an asset path relative to the paper's `assets/`. For an interactive replacement,
register a Svelte renderer by stable manuscript label in `exhibits/index.ts`.
Use ddl-charts primitives and tokens. Retain captions, units, uncertainty information,
and notes; interactions must preserve the result's meaning.

Additional editorial explanations belong in separate context panels or visibly
identified introductions. An original technical passage can move into an expandable
block without changing its wording. Read docs/features.md when selecting interactions.

Completion: each scientific exhibit and every selectable state is traceable to its
inputs and code, and original captions and notes have been preserved.

## 4. Reproduce

Reuse code from the original research project or rebuild calculations in Python,
as the Nobel example does. Include the complete dependency closure in `reproduction/`:
inputs, analysis code, required libraries, expected outputs and one entry point.
Provide a `--check` mode comparing fresh results with the displayed data. Keep random
seeds fixed and explain tolerances. Copying a result file is not a numerical reproduction.

Record published-table transcriptions and external metadata as explicit manual inputs.
Keep their source/version and validate the copy; distinguish this from re-estimation.
If required data cannot be redistributed, resolve access or choose a different exhibit
with the author before claiming the bundle is complete.

Completion: every displayed scientific exhibit, including sidebar and explorer states,
is covered by a working reproduction check. The downloaded bundle works independently
of this repo and of the original private research checkout.

## 5. Preserve rights and handle sensitive material

Read the root COPYRIGHT.md. Its MIT and CC0 grants cover reusable starter material;
they do not cover the real manuscript, figures, tables, captions, notes or new
paper-specific explanations. Preserve that exclusion when replacing fictional content.
Do not carry a fictional example's CC0 notice over to real research inputs or writing.

Record the manuscript version and rights holder in the paper's COPYRIGHT.md, and carry
relevant rights notices into `reproduction/` so downloaded bundles remain clear on scope.
Retain imported code/data licenses. License new analysis code or data separately only
with the author's authorization and the necessary rights. Technical documentation for
software must not sweep manuscript text or exhibit notes into a software license.

Before public hosting, check the journal's policies and any signed agreement for the
specific version, host, embargo and required notice. Do not assume preprint permission
also covers accepted manuscripts or publisher PDFs. Do not add a paper-wide open license
in anticipation of a later copyright transfer: prior valid grants generally cannot be
withdrawn by deleting their notice. Flag existing open licenses for the author's review.

Submission pages may use real journal names as labels. Fill the placeholder letters,
reports or responses only after explicit permission to publish the specific material.
Check content JSON, images, downloads and source snapshots as well as original documents.
Never include credentials, internal correspondence or copied machine configuration.

## 6. Review and revise

Run checks and static builds for the selected paper, and its reproduction check.
Ask the author to run the dev server and review presentation. When a manuscript changes,
compare source versions, update only affected source-derived content, and preserve existing
editorial additions. Never regenerate everything over manual additions.

Keep a fidelity inventory linking passages and exhibits to source versions and recording
author-authorized substantive edits. Before publication, confirm source fidelity,
reproduction coverage, redistribution terms and the user's deployment authorization.
