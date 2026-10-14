<!-- Map each interaction to its live example and implementation; depends on the Nobel example registry. -->
# Feature index

Run `npm run dev` for Nobel. Paths below are local
site routes; implementation paths are relative to the repository.

| Feature | Example / route | Implementation |
|---|---|---|
| Guided landing chart and pinned laureate card | Nobel `/` | `examples/nobel/exhibits/LandingScrolly.svelte`, `NobelRankScatter.svelte` |
| Section navigation and reading progress | Nobel sections | `src/lib/reading/SectionNav.svelte`, `ReadingProgress.svelte` |
| Search with navigation to matching text | Nobel, header | `SearchBox.svelte`, `src/lib/search/` |
| Citations and linked references | Nobel sections | `Citation.svelte` |
| Footnote previews and backlinks | Nobel sections | `FootnoteRef.svelte`, `SectionBody.svelte` |
| Expandable technical material | Nobel sections | `SectionBody.svelte` collapsible blocks |
| FAQ accordions | Nobel `/faq` | `FaqList.svelte` |
| Context-panel text and images | Nobel numbered tags | `AnnotationPanel.svelte` |
| Interactive sidebar and expanded appendix | Nobel A4 and other tags | `AnnotationPanel.svelte`, `RankWalkthrough.svelte` |
| Graph tabs and series toggles | Nobel `/results`, supplementary tags | `FigureRankHistograms.svelte`, `FigureBinscatterRanks.svelte`, `FigurePermTest.svelte` |
| Five-row raw data; sort, filter, pagination, expandable evidence | Nobel `/data-explorer` | `NobelistsDataTable.svelte` |
| Intermediate data-building exploration and crosswalks | Nobel `/occupation-rank-explorer` | `OccupationRankChart.svelte`, `OccupationTable.svelte` |
| Coordinated subgroup/measure controls | Nobel `/extended-results` | `ExtendedResultsExplorer.svelte` |
| Submission navigation and permission placeholders | Nobel `/referee-comments-and-responses` | `RefereeResponses.svelte` |
| Independent reproduction archive and individual files | Nobel `/replication` | `scripts/prepare-paper.mjs`, replication route |
| Markdown paper export | Nobel `/paper.md` | `src/lib/content/markdown.ts` |
| Source PDF | Nobel header | `examples/nobel/assets/paper/` |
| Responsive/mobile navigation and context panels | Nobel | `src/routes/+layout.svelte`, aside modules |

Shared implementations are in `src/lib/reading/`; Nobel scientific implementations
are in `examples/nobel/exhibits/`. Register custom figures, panels and explorer pages
in the active paper's `exhibits/index.ts`. The example covers interaction types;
you need not bring every Nobel-specific exhibit into a new paper.
