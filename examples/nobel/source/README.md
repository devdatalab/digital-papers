<!-- Explain the fidelity snapshots without retaining unused or private manuscript material. -->
# Source snapshots

`sections/` contains the original digital-publication wording retained by this excerpt,
including original footnotes, references and annotation content. These snapshots were
selected from the copied publication before restructuring. They are not output from
an importer. Omitted passages are not retained here, and actual submission correspondence
is excluded entirely.

`meta.json` records the original title/author metadata. `manifest.json` records original
section order. `inventory.json` maps retained sections to snapshots; `exhibits.json` lists
the displayed main and sidebar exhibits. `../assets/paper/nobel_prizes.pdf` is the supplied
source PDF. The retained Galton illustration was restored from the original public
publication's `/annotations/galton-1874.png` asset and keeps its original annotation caption.

Run `npm run verify` to compare retained wording with these snapshots. This checks
preservation of the original digital text, not agreement between all versions of the
working paper. Published-table transcriptions in the reproduction bundle identify their
own PDF versions and deliberately preserve existing version differences.

These research texts and the source PDF are excluded from the starter's MIT/CC0 grants;
see the root COPYRIGHT.md. The official Nobel publication remains independent.
