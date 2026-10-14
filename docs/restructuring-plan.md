<!-- Record the approved scope and implementation handoff; depends on the examples and verification commands. -->
# Approved restructuring and local handoff

The project is a cloneable starter for a researcher using a local coding agent. It has
one shared SvelteKit app, a minimal fictional example, a slim Nobel feature showcase,
and a working author template. There is no manuscript importer, package-upgrade mechanism,
or connection to the official Nobel site's deployment.

The work is local only: no commits, pushes, remote changes or deployment.

## Implemented

- Removed personal task folders/instructions, internal plans, actual referee material,
  the legacy importer, unused external-data tooling, recent-laureate and errata features.
- Relocated scientific renderers, inputs and code into the Nobel example.
- Replaced hardcoded figure dispatch with selected-paper registrations.
- Added instructional minimal content and an editable `papers/my-paper/` template.
- Preserved retained scientific text and notes; marked omissions and instructional copy.
- Kept the first three real journal labels with correspondence/permission placeholders.
- Retained five-row raw exploration, occupation/intermediate-data exploration, extended
  results, expandable appendices, interactive sidebars, tabs/toggles, citations and footnotes.
- Added independent reproduction bundles and per-exhibit lineage, including declared
  manual published-table inputs and direct CSV extraction for walkthrough/country counts.
- Removed Git-dependent build hooks; startup and builds work without Git history.
- Added neutral branding and removable Development Data Lab footer credit.
- Added MIT software terms, CC0 original design/instruction terms and research exclusions.
- Made hosting local-first, documented static hosts and provided minimal-only manual Pages deployment.

## Verification and remaining author review

Passed: Svelte checks with zero errors or warnings; root and subpath static builds;
fictional and Nobel reproduction; independently extracted Nobel reproduction; and
source/public-file audits. The final build output is the minimal example at the root path.
The numerical comparison policy is documented in the Nobel reproduction README.

Browser automation is excluded by the repository convention. The author should review
both examples locally, particularly mobile navigation, sidebar expansion and chart controls.
A trial with the next real research paper remains the release validation step; no second
research project's source files were supplied or read during this restructuring.

Publishing the repository or the optional example is a separate authorized action.
