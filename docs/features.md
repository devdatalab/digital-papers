<!-- Map each interaction to its live example and implementation; depends on both example registries. -->
# Feature index

Run `npm run dev` for Minimal or `npm run dev:nobel` for Nobel. Paths below are local
site routes; implementation paths are relative to the repository.

| Feature | Example / route | Implementation |
|---|---|---|
| Neutral cover and starting paper | Minimal `/` | `examples/minimal/exhibits/Cover.svelte` |
| Guided landing chart and pinned laureate card | Nobel `/` | `examples/nobel/exhibits/LandingScrolly.svelte`, `NobelRankScatter.svelte` |
| Section navigation and reading progress | Both sections | `src/lib/reading/SectionNav.svelte`, `ReadingProgress.svelte` |
| Search with navigation to matching text | Both, header | `SearchBox.svelte`, `src/lib/search/` |
| Citations and linked references | Minimal `/introduction`, Nobel sections | `Citation.svelte` |
| Footnote previews and backlinks | Minimal `/introduction`, Nobel sections | `FootnoteRef.svelte`, `SectionBody.svelte` |
| Linked figure/table references | Minimal `/results` | `src/lib/content/index.ts`, `SectionBody.svelte` |
| Expandable technical material | Minimal `/introduction`, Nobel sections | `SectionBody.svelte` collapsible blocks |
| FAQ accordions | Both `/faq` | `FaqList.svelte` |
| Context-panel text and images | Nobel numbered tags | `AnnotationPanel.svelte` |
| Interactive sidebar and expanded appendix | Minimal A2; Nobel A4 and other tags | `AnnotationPanel.svelte`, `RankWalkthrough.svelte` |
| Graph tabs and series toggles | Nobel `/results`, supplementary tags | `FigureRankHistograms.svelte`, `FigureBinscatterRanks.svelte`, `FigurePermTest.svelte` |
| Small reproducible chart and table | Minimal `/results` | `CompareGroups.svelte`, `SummaryTable.svelte` |
| Five-row raw data; sort, filter, pagination, expandable evidence | Nobel `/data-explorer` | `NobelistsDataTable.svelte` |
| Intermediate data-building exploration and crosswalks | Nobel `/occupation-rank-explorer` | `OccupationRankChart.svelte`, `OccupationTable.svelte` |
| Coordinated subgroup/measure controls | Nobel `/extended-results` | `ExtendedResultsExplorer.svelte` |
| Submission navigation and permission placeholders | Nobel `/referee-comments-and-responses` | `RefereeResponses.svelte` |
| Independent reproduction archive and individual files | Both `/replication` | `scripts/prepare-paper.mjs`, replication route |
| Markdown paper export | Both `/paper.md` | `src/lib/content/markdown.ts` |
| Source PDF | Nobel header | `examples/nobel/assets/paper/` |
| Responsive/mobile navigation and context panels | Both | `src/routes/+layout.svelte`, aside modules |

Shared implementations are in `src/lib/reading/`; Nobel scientific implementations
are in `examples/nobel/exhibits/`. Register custom figures, panels and explorer pages
in the active paper's `exhibits/index.ts`. The examples cover interaction types;
you need not bring every Nobel-specific exhibit into a new paper.
