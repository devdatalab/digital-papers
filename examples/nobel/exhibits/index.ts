/** Register Nobel-specific exhibits and pages; consumed by the shared renderer. */
import type { Component } from 'svelte';
import FigureRankHistograms from './FigureRankHistograms.svelte';
import FigureBinscatterRanks from './FigureBinscatterRanks.svelte';
import FigurePermTest from './FigurePermTest.svelte';
import TableMainSpec from './TableMainSpec.svelte';
import TableHeterogeneity from './TableHeterogeneity.svelte';
import TableParentFieldMatch from './TableParentFieldMatch.svelte';
import DataExplorer from './pages/data-explorer.svelte';
import OccupationExplorer from './pages/occupation-rank-explorer.svelte';
import ExtendedResults from './pages/extended-results.svelte';
export { default as Cover } from './Cover.svelte';
export { appendixComponents as panels } from './appendixRegistry';
// Each exhibit owns its props; registrations keep the shared renderer paper-agnostic.
export const figures: Record<string, Component<any>> = {
  'fig:rank_histograms': FigureRankHistograms,
  'fig:inc_educ_ranks': FigureBinscatterRanks,
  'fig:perm_main': FigurePermTest,
  'tab:main_spec': TableMainSpec,
  'tab:heterogeneity': TableHeterogeneity,
  'tab:parent_child_field_match': TableParentFieldMatch
};
export const pages: Record<string, Component<any>> = {
  'data-explorer': DataExplorer,
  'occupation-rank-explorer': OccupationExplorer,
  'extended-results': ExtendedResults
};
