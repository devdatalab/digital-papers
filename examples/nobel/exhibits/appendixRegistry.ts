/** Register Nobel supplemental exhibits for the shared context panel.
 * Depends on the scientific renderers in this example folder. */
import type { Component } from 'svelte';
import FigureBinscatterRanks from './FigureBinscatterRanks.svelte';
import FigurePermTest from './FigurePermTest.svelte';
import FigureMostCommonOccup from './FigureMostCommonOccup.svelte';
import FigureBelowThreshold from './FigureBelowThreshold.svelte';
import FigureFieldMatch from './FigureFieldMatch.svelte';
import AppendixTable from './AppendixTable.svelte';
import RankWalkthrough from './RankWalkthrough.svelte';
import OccupationPrizeShareChart from './OccupationPrizeShareChart.svelte';

/** Keyed by the `component` string on an AnnotationBlock of type 'component'.
 *  `Component<any>` because each entry accepts its own bespoke prop shape; the
 *  content JSON supplies matching `props`. */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const appendixComponents: Record<string, Component<any>> = {
	// App. figure: father-rank trend by birth cohort. Reuses the main-text
	// binscatter with xAxis='cohort' (props supplied by the content JSON).
	FigureBinscatterRanks,
	// App. figure: parent–child field-match permutation test across the extra
	// match definitions. Reuses the main-text Figure 3 component with a `panels`
	// prop selecting the professor / non-professor / weak-match samples.
	FigurePermTest,
	// App. figure: most common father occupations vs. the population.
	FigureMostCommonOccup,
	// App. figure: share of laureates with fathers below the 80th/90th pctile.
	FigureBelowThreshold,
	// App. figure: per-discipline share whose father was in a matching field.
	FigureFieldMatch,
	// All appendix tables share this generic renderer; the `table` prop selects
	// the spec in appendixTables.ts.
	AppendixTable,
	// A4 Data-and-Methods walkthrough: how a father's occupation becomes a
	// national and global income rank, on four contrasting laureates. No props.
	RankWalkthrough,
	// "Father occupation across Nobel fields" pane (A10): per-group census / all /
	// per-field father-occupation shares, two selectors (props: { compact: true }).
	OccupationPrizeShareChart
};
