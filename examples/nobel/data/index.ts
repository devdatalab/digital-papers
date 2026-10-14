/** Typed access to the Nobel example’s committed scientific exports.
 * Rebuild/check with examples/nobel/reproduction/make_all.py. */

import data from './nobelists.json';
import rankHistogramsRaw from './rank_histograms.json';
import binscatterRanksRaw from './binscatter_ranks.json';
import mainSpecRaw from './main_spec.json';
import mainRobustRaw from './main_robust.json';
import heterogeneitySpecRaw from './heterogeneity_spec.json';
import permTestRaw from './parent_field_perm_test.json';
import matchSharesRaw from './parent_field_match_shares.json';
import mostCommonOccupationsRaw from './most_common_occupations.json';
import otherRankFunctionsRaw from './other_rank_functions.json';
import heteroTrendsRaw from './hetero_trends.json';
import regionalAnalysisRaw from './regional_analysis.json';
import occShares10Raw from './occ_shares_10group.json';
import occShares25Raw from './occ_shares_25group.json';
import occPrizeSharesRaw from './occ_prize_shares.json';
import occupationListRaw from './occupation_list.json';
import occShares1950ListRaw from './occ_shares_occ1950_list.json';
import genderAnalysisRaw from './gender_analysis.json';
import genderSpecRobustRaw from './gender_spec_robust.json';
import occRankTimeseriesRaw from './occ_rank_timeseries.json';
import rankWalkthroughRaw from './rank_walkthrough.json';
import extendedResultsRaw from './extended_results.json';
import countryListRaw from './country_list.json';

/** A y-axis rank metric the user can toggle between. */
export interface Metric {
	/** Matches a key inside each row's `ranks` object. */
	key: string;
	/** Dropdown label. */
	label: string;
	/** Y-axis label shown when this metric is active. */
	axisLabel: string;
}

/** One laureate-prize row (one dot in the scatter). */
export interface NobelRow {
	id: number;
	name: string;
	year: number;
	category: string;
	country: string;
	fatherOcc: string;
	awardAge: number | null;
	share: number | null;
	gender: string;
	/** Rank value (0–100 percentile) per metric key; null when unavailable. */
	ranks: Record<string, number | null>;
	// --- Gemini grounded-search provenance for the father's occupation. ---
	/** Occupation the grounded search found (may differ from `fatherOcc`). */
	foundOcc: string;
	/** Direct supporting quote from a source. */
	evidenceQuote: string;
	/** The search's reasoning for the classification (a paragraph). */
	occReasoning: string;
	/** Source URLs consulted, in the order the search reported them. */
	sources: string[];
}

export interface NobelDataset {
	meta: { n: number; yearMin: number; yearMax: number; generatedFrom: string };
	metrics: Metric[];
	rows: NobelRow[];
}

const dataset = data as NobelDataset;

export const nobelRows: NobelRow[] = dataset.rows;
export const nobelMetrics: Metric[] = dataset.metrics;
export const nobelMeta = dataset.meta;

/** The four prize categories, in a stable display order. */
export const PRIZE_CATEGORIES = ['Physics', 'Chemistry', 'Medicine', 'Economics'] as const;
export type PrizeCategory = (typeof PRIZE_CATEGORIES)[number];

// ---------------------------------------------------------------------------
// rank_histograms.json  (Figure 1 — rank histogram, 3 panels)
// ---------------------------------------------------------------------------

export interface HistogramBin {
	x: number; // percentile midpoint (2.5, 7.5, …, 97.5)
	pct: number; // share of laureates in this bin (0–100)
}
export interface RankHistogramSeries {
	label: string;
	full: HistogramBin[];
	male: HistogramBin[];
	female: HistogramBin[];
}
export interface RankHistogramsData {
	meta: { script: string; generated: string; n: number };
	data: Record<string, RankHistogramSeries>;
}
export const rankHistogramsData = rankHistogramsRaw as unknown as RankHistogramsData;

// ---------------------------------------------------------------------------
// binscatter_ranks.json  (Figure 2 — binscatter + lfit, 3 panels)
// ---------------------------------------------------------------------------

export interface BinscatterBin {
	x: number; // prize year (bin mean)
	y: number; // rank (bin mean)
}
export interface Lfit {
	coef: number;
	intercept: number;
	pred_start: { x: number; y: number };
	pred_end: { x: number; y: number };
	r2: number;
	/** Prize-year series only — predictions at the paper's 1901/2023 anchors.
	 *  Absent on the by_cohort series, which uses pred_start/pred_end instead. */
	pred_1901?: number;
	pred_2023?: number;
	diff_1901_2023?: number;
}
export interface BinscatterSeries {
	bins: BinscatterBin[];
	lfit: Lfit;
}
export interface BinscatterRankEntry {
	label: string;
	by_prize_year: BinscatterSeries;
	by_cohort: BinscatterSeries;
}
export interface BinscatterRanksData {
	meta: Record<string, unknown>;
	data: Record<string, BinscatterRankEntry>;
}
export const binscatterRanksData = binscatterRanksRaw as unknown as BinscatterRanksData;

// ---------------------------------------------------------------------------
// main_spec.json  (Table 1 — OLS secular trends)
// ---------------------------------------------------------------------------

export interface MainSpecRow {
	label: string;
	column: string;
	coef: number;
	se: number;
	intercept: number;
	/** SE of the constant. Only panel A14 (PDF Table A7) prints it; Table 1 omits
	 *  the constant row entirely. */
	intercept_se: number;
	n: number;
	sample_mean: number;
	r2: number;
}
export interface MainSpecData {
	meta: Record<string, unknown>;
	data: Record<string, MainSpecRow>;
}
export const mainSpecData = mainSpecRaw as unknown as MainSpecData;

// ---------------------------------------------------------------------------
// main_robust.json  (PDF Appendix Tables A5/A6 — robustness variants of Table 1)
// ---------------------------------------------------------------------------

/** One trend regression: constant at prize year 1901 plus the annual slope.
 *  `stars` is computed by the generator from exact p-values and is the
 *  authoritative marker for the trend. `constant_stars` is carried for parity
 *  with the JSON but deliberately not rendered — see `levelCell` in
 *  `$lib/components/appendixTables`. */
export interface RobustReg {
	column: string;
	constant: number;
	constant_se: number;
	constant_stars: string;
	coef: number;
	se: number;
	stars: string;
	n: number;
	r2: number;
}
/** One panel. PDF Table A6 Panels B and C recode education only, so they carry no
 *  `income` key — the published table leaves those cells blank. */
export interface RobustPanel {
	title: string;
	education: RobustReg;
	income?: RobustReg;
}
export interface MainRobustData {
	meta: Record<string, unknown>;
	data: {
		a5: Record<string, RobustPanel>;
		a6: Record<string, RobustPanel>;
	};
}
export const mainRobustData = mainRobustRaw as unknown as MainRobustData;

// ---------------------------------------------------------------------------
// heterogeneity_spec.json  (Table 2 — group means by gender/category/region)
// ---------------------------------------------------------------------------

export interface GroupStats {
	group: number;
	mean: number;
	se: number;
	n: number;
}
export interface FullSampleStats {
	mean: number;
	se: number;
	n: number;
}
export type HeteroPanel = Record<string, GroupStats | number>;
export interface HeteroOutcome {
	full_sample: FullSampleStats;
	gender: HeteroPanel;
	bloc: HeteroPanel;
	region: HeteroPanel;
	prize_category: HeteroPanel;
}
export interface HeterogeneitySpecData {
	meta: {
		script: string;
		generated: string;
		n: number;
		labels: {
			region: Record<string, string>;
			bloc: Record<string, string>;
			prize_category: Record<string, string>;
		};
	};
	data: Record<string, HeteroOutcome>;
}
export const heterogeneitySpecData = heterogeneitySpecRaw as unknown as HeterogeneitySpecData;

// ---------------------------------------------------------------------------
// parent_field_perm_test.json  (Figure 3 — permutation test histogram)
// ---------------------------------------------------------------------------

export interface PermHistBin {
	bin_center: number;
	fraction: number;
}
export interface PermTestEntry {
	n: number;
	parent_counts: Record<string, number>;
	n_observed: number;
	observed_share: number;
	observed_pct: number;
	expected_count: number;
	expected_pct: number;
	excess_rate: number;
	p_value: number;
	p_value_display: string;
	sim_histogram: PermHistBin[];
	sim_mean: number;
	sim_std: number;
}
export interface PermTestData {
	meta: Record<string, unknown>;
	data: Record<string, PermTestEntry>;
}
export const permTestData = permTestRaw as unknown as PermTestData;

// ---------------------------------------------------------------------------
// parent_field_match_shares.json  (App. figure — field-match shares by field)
//   Keyed <quality>_<field> (e.g. good_match_physics). Each entry carries a
//   `bars` array: the census baseline, the overall laureate share, and the
//   share broken out by laureate field. (The randomization-test summary lives
//   in parent_field_perm_test.json / permTestData, not here.)
// ---------------------------------------------------------------------------

export interface MatchShareBar {
	/** census | overall | chemistry | physics | medicine | economics */
	row_id: string;
	label: string;
	/** Percentage on a 0–100 scale. */
	share: number;
	count: number | null;
}
export interface MatchSharesEntry {
	quality: string;
	field: string;
	n_context: number;
	n_selected: number;
	census_share: number;
	bars: MatchShareBar[];
}
export interface MatchSharesData {
	meta: Record<string, unknown>;
	data: Record<string, MatchSharesEntry>;
}
export const matchSharesData = matchSharesRaw as unknown as MatchSharesData;

// ===========================================================================
// Appendix outputs — surfaced as right-pane "Additional Information" panels.
// See docs/replication/appendix_integration_plan.md. Deeply-nested regression
// trees are typed with the shared CoefSe/RegressionBlock primitives below and
// Record<> for the data-driven intermediate keys, matching the HeteroPanel
// convention above; flat list/table shapes are typed in full.
// ===========================================================================

/** One estimated coefficient with its standard error. */
export interface CoefSe {
	coef: number;
	se: number;
}
/** A regression's term→CoefSe map plus scalar diagnostics (n, r2). Terms carry
 *  a CoefSe; `n`/`r2` (and similar) are bare numbers — same union shape as
 *  HeteroPanel above. */
export type RegressionBlock = Record<string, CoefSe | number>;

// ---------------------------------------------------------------------------
// most_common_occupations.json  (App. figure — most common father occupations)
// ---------------------------------------------------------------------------

export interface MostCommonOccRow {
	rank: number;
	// Broad occupation group key (e.g. "Managers"); the dataset reclassified this
	// from a numeric microocc code to a string group. `occ1950` is the first
	// occ1950 code seen in the group. Neither is rendered — `label` is.
	microocc: string;
	occ1950: number | null;
	label: string;
	occ1950_label: string;
	count: number;
	nobelists_pct: number;
	census_pct: number;
	occ_share_ratio: number;
}
export interface MostCommonOccupationsData {
	meta: Record<string, unknown>;
	data: {
		top10: MostCommonOccRow[];
		stacked: { rows: MostCommonOccRow[] };
	};
}
export const mostCommonOccupationsData =
	mostCommonOccupationsRaw as unknown as MostCommonOccupationsData;

// ---------------------------------------------------------------------------
// other_rank_functions.json  (App. figure — share below 80th/90th pctile)
// ---------------------------------------------------------------------------

export interface BinPoint {
	x: number;
	y: number;
}
export interface BelowThresholdSeries {
	column: string;
	binscatter: BinPoint[];
}
export interface OtherRankFunctionsData {
	meta: Record<string, unknown>;
	data: {
		/** Keyed p80 / p90, then by outcome (med_inctot, educ, global_med_inctot). */
		below_threshold: Record<string, Record<string, BelowThresholdSeries>>;
		/** Median rank per prize-year bin, keyed by rank metric. */
		median_by_bin: Record<string, BinPoint[]>;
	};
}
export const otherRankFunctionsData = otherRankFunctionsRaw as unknown as OtherRankFunctionsData;

// ---------------------------------------------------------------------------
// hetero_trends.json  (App. Table — secular trend slopes by subgroup)
// ---------------------------------------------------------------------------

export interface TrendSlope {
	coef: number;
	se: number;
	n?: number;
}
/** Per-outcome trend estimates. full_sample is a single slope; gender/category/
 *  region hold one slope per group plus scalar `p_equal`/`n` (hence the union). */
export interface HeteroTrendOutcome {
	full_sample: TrendSlope;
	gender: Record<string, TrendSlope | number>;
	category: Record<string, TrendSlope | number>;
	region: Record<string, TrendSlope | number>;
}
export interface HeteroTrendsData {
	meta: Record<string, unknown>;
	data: Record<string, HeteroTrendOutcome>;
}
export const heteroTrendsData = heteroTrendsRaw as unknown as HeteroTrendsData;

// ---------------------------------------------------------------------------
// regional_analysis.json  (App. Table — top-percentile shares by region)
// ---------------------------------------------------------------------------

export interface RegionalAnalysisData {
	meta: Record<string, unknown>;
	data: {
		region_spec: Record<string, unknown>;
		bloc_spec: Record<string, unknown>;
		/** Keyed decile / 5pct, then by outcome → regression block. */
		region_top_pctl: Record<string, Record<string, RegressionBlock>>;
		bloc_interaction: Record<string, unknown>;
		binscatter_bloc: Record<string, unknown>;
	};
}
export const regionalAnalysisData = regionalAnalysisRaw as unknown as RegionalAnalysisData;

// ---------------------------------------------------------------------------
// occ_shares_10group.json / occ_shares_25group.json
//   (App. Tables — laureate vs. census occupation shares, coarse/fine groups)
// ---------------------------------------------------------------------------

export interface OccShareGroupRow {
	/** Present in the 10-group file only. */
	occ1950_1?: number;
	label: string;
	occ_count: number;
	laureate_n: number;
	laureate_share: number;
	laureate_pct: number;
	census_share: number;
	census_pct: number;
	avg_educ_rank: number;
	avg_med_inctot_rank: number;
	avg_global_med_inctot_rank: number;
	overrep_ratio: number;
}
export interface OccSharesGroupData {
	meta: Record<string, unknown>;
	data: OccShareGroupRow[];
}
export const occShares10Data = occShares10Raw as unknown as OccSharesGroupData;
export const occShares25Data = occShares25Raw as unknown as OccSharesGroupData;

// ---------------------------------------------------------------------------
// occ_prize_shares.json
//   (Annotation pane — father-occupation share by Nobel field, per group)
// ---------------------------------------------------------------------------

export type OccPrizeLevelId = 'group_10' | 'group_25' | 'occ1950';

export interface OccPrizeShareGroup {
	id: string;
	label: string;
	sort_order: number;
	laureate_n: number;
	census_pct: number;
	/** Keys: "all" plus each Nobel field in meta.fields. Values are percentages. */
	shares: Record<string, number>;
}
export interface OccPrizeLevel {
	label: string;
	groups: OccPrizeShareGroup[];
}
export interface OccPrizeSharesData {
	meta: { script: string; fields: string[]; n_total: number; n_matched: number };
	levels: Record<OccPrizeLevelId, OccPrizeLevel>;
}
export const occPrizeSharesData = occPrizeSharesRaw as unknown as OccPrizeSharesData;

// ---------------------------------------------------------------------------
// occupation_list.json  (App. Table — occupation → group crosswalk)
// ---------------------------------------------------------------------------

export interface OccupationListEntry {
	label: string;
	group_10: string;
	group_25: string;
}
export interface OccupationListData {
	meta: Record<string, unknown>;
	/** Keyed by stringified row index. */
	data: Record<string, OccupationListEntry>;
}
export const occupationListData = occupationListRaw as unknown as OccupationListData;

// ---------------------------------------------------------------------------
// occ_shares_occ1950_list.json  (App. Table — full occ1950 correspondence)
// ---------------------------------------------------------------------------

export interface Occ1950Row {
	occ1950: number;
	label: string;
	display: string;
	group_10: string;
	group_10_id: number;
	group_25: string;
	group_6: string;
	educ_rank: number;
	med_inctot_rank: number;
	global_med_inctot_rank: number;
	laureate_n: number;
	laureate_share: number;
	laureate_pct: number;
	census_share: number;
	census_pct: number;
	overrep_ratio: number;
}
export interface Occ1950ListData {
	meta: Record<string, unknown>;
	data: Occ1950Row[];
}
export const occShares1950ListData = occShares1950ListRaw as unknown as Occ1950ListData;

// ---------------------------------------------------------------------------
// gender_analysis.json  (App. Tables/figures — gender robustness)
// ---------------------------------------------------------------------------

export interface GenderSpecCell {
	Intercept: CoefSe;
	prize_year_rescaled: CoefSe;
	n: number;
	r2: number;
}
export interface GenderDistTest {
	n_male: number;
	n_female: number;
	p_wilcoxon: number;
	mean_male: number;
	mean_female: number;
}
export interface GenderAnalysisData {
	meta: Record<string, unknown>;
	data: {
		/** Per-outcome male/female trend regressions. */
		gender_spec: Record<string, Record<string, GenderSpecCell>>;
		/** HC1-robust Wald F-tests of equal male/female prize-year slopes. */
		slope_tests: Record<string, { p_equal_slopes: number; difference_female_minus_male: CoefSe; n: number }>;
		/** Per-outcome Wilcoxon distribution tests. */
		dist_tests: Record<string, GenderDistTest>;
	};
}
export const genderAnalysisData = genderAnalysisRaw as unknown as GenderAnalysisData;

// ---------------------------------------------------------------------------
// gender_spec_robust.json  (PDF Appendix Table A8 — gender gap, four exclusion
//   samples). One `female ~ outcome` OLS (HC1) per sample × outcome, mirroring
//   the Table 2 / heterogeneity Panel A specification. Surfaced as annotation
//   panel A3 on the Data & Methods page.
// ---------------------------------------------------------------------------

/** One `outcome ~ female` regression: the female coefficient (female − male
 *  baseline) with its HC1 SE and p-value, plus the intercept (baseline male
 *  level) and N. `p` is stored for every outcome, but the spec renders stars
 *  only on the four Top-N indicator outcomes — see `genderSpecRobustSpec` in
 *  `$lib/components/appendixTables`, matching the published table. */
export interface GenderRobustReg {
	constant: number;
	constant_se: number;
	coef: number;
	se: number;
	p: number;
	n: number;
}
/** One exclusion sample: title, panel N, and the six outcome regressions keyed
 *  by outcome column (med_inctot_rank, educ_rank, top_decile_*, top_20pct_*). */
export interface GenderRobustPanel {
	title: string;
	n: number;
	outcomes: Record<string, GenderRobustReg>;
}
export interface GenderSpecRobustData {
	meta: Record<string, unknown>;
	/** Panels keyed A–D (excl. difficult / aristocrats / business+farmers / econ). */
	data: Record<string, GenderRobustPanel>;
}
export const genderSpecRobustData = genderSpecRobustRaw as unknown as GenderSpecRobustData;

// ---------------------------------------------------------------------------
// occ_rank_timeseries.json  (Occupation Explorer trajectories)
// ---------------------------------------------------------------------------

export type OccupationRankLevelId = 'occgroup_10' | 'occgroup_25' | 'occ1950';

export interface OccupationRankPoint {
	year: number;
	income_rank: number | null;
	education_rank: number | null;
	sample_count: number | null;
}

export interface OccupationRankOption {
	id: string;
	label: string;
	sort_order: number;
	member_count: number;
	laureate_n: number;
}

export interface OccupationRankLevel {
	label: string;
	options: OccupationRankOption[];
	by_id: Record<string, { rows: OccupationRankPoint[] }>;
}

export interface OccupationRankTimeseriesData {
	meta: {
		country: 'USA';
		year_min: number;
		year_max: number;
		rank_scale: [number, number];
		group_weight: 'n_cohort_occ_raw';
	};
	levels: Record<OccupationRankLevelId, OccupationRankLevel>;
}

export const occupationRankTimeseriesData =
	occRankTimeseriesRaw as unknown as OccupationRankTimeseriesData;

// ---------------------------------------------------------------------------
// rank_walkthrough.json  (A4 — Data-and-Methods rank-calculation explainer)
// ---------------------------------------------------------------------------

/** One laureate's real intermediate + final income-rank values, for the A4
 *  Data-and-Methods walkthrough. All fields are extracted from
 *  nobelists_analysis.csv (see rank_walkthrough.json `meta`); nothing is
 *  recomputed in the app. */
export interface RankWalkthroughLaureate {
	id: string;
	name: string;
	/** Surname used on the selector pill. */
	short: string;
	category: string;
	prizeYear: number;
	country: string;
	/** True when born in the U.S. (matched decade == birth decade, no GDP adjustment). */
	usBorn: boolean;
	/** Father's occupation as recorded in the source. */
	fatherOccupation: string;
	/** Standardised census occupation category. */
	occ1950Label: string;
	birthDecade: number;
	/** U.S. census decade the country-decade was matched to. */
	matchedDecade: number;
	/** Country income level relative to the U.S. in the birth decade (1.0 for U.S.). */
	gdpRatio: number;
	nationalIncomeRank: number;
	globalIncomeRank: number;
	educationRank: number;
	prestigeRank: number;
}

export interface RankWalkthroughData {
	meta: { source: string; note: string; columns: string[] };
	laureates: RankWalkthroughLaureate[];
}

export const rankWalkthroughData = rankWalkthroughRaw as unknown as RankWalkthroughData;

// ---------------------------------------------------------------------------
// extended_results.json  (Extended Results Explorer — SES measure × outcome ×
//   subgroup grid, /extended-results Extras page)
//   cells[measureId][subgroupId] holds a father-rank histogram + three prize-year
//   trend panels (average_rank, top_10, top_20). Region subgroups are omitted
//   under the global_income measure. See scripts/site-data/generators/extended_results/.
// ---------------------------------------------------------------------------

export interface ExtendedMeasure {
	id: string;
	label: string;
	/** Source column in nobelists_analysis.csv. */
	column: string;
	/** Short label for compact controls. */
	short: string;
}
export interface ExtendedSubgroup {
	dim: 'overall' | 'field' | 'gender' | 'region';
	id: string;
	label: string;
}
export interface ExtendedHistogramBar {
	x: number; // 5-pt bin center (2.5 … 97.5)
	binStart: number;
	binEnd: number;
	share: number; // % of laureates in this bin
	n: number;
}
export interface ExtendedTrendPoint {
	x: number; // prize-year window midpoint
	binStart: number;
	binEnd: number;
	y: number; // mean rank, or top-share (%) for the top_10/top_20 panels
	n: number;
}
/** Linear trend fit. Values are null when the sample was too thin to fit; the
 *  predStart/predEnd endpoints are evaluated at 1901/2023 (out-of-sample OK). */
export interface ExtendedFit {
	intercept: number | null;
	coef: number | null;
	se: number | null;
	p: number | null;
	predStart: { x: number; y: number | null };
	predEnd: { x: number; y: number | null };
}
export interface ExtendedPanel {
	points: ExtendedTrendPoint[];
	fit: ExtendedFit;
}
export type ExtendedPanelId = 'average_rank' | 'top_10' | 'top_20';
export interface ExtendedCell {
	n: number;
	histogram: ExtendedHistogramBar[];
	panels: Record<ExtendedPanelId, ExtendedPanel>;
}
export interface ExtendedResultsData {
	meta: Record<string, unknown>;
	measures: ExtendedMeasure[];
	subgroups: ExtendedSubgroup[];
	/** cells[measureId][subgroupId]; region subgroups absent under global_income. */
	cells: Record<string, Record<string, ExtendedCell>>;
}
export const extendedResultsData = extendedResultsRaw as unknown as ExtendedResultsData;

// ---------------------------------------------------------------------------
// country_list.json  (Panel A15 — "Countries in each region")
//   The list of laureate birth countries grouped by the analysis region bloc
//   (West / East / Global South) actually used in the regional regressions.
//   Curated from nobelists_analysis.csv — one laureate per row — rather than the
//   paper's printed A11, which is a wider modern-country crosswalk not derivable
//   from the analysis data (see docs/replication/unresolved_cross_references.md).
// ---------------------------------------------------------------------------

/** One country within a region, with its laureate count in the analysis sample. */
export interface CountryListCountry {
	country: string;
	laureates: number;
}
/** One region bloc and the countries filed under it, ordered by laureate count. */
export interface CountryListRegion {
	/** Analysis bloc code: `west` | `east` | `south`. */
	bloc: string;
	/** Display label: "West" | "East" | "Global South". */
	label: string;
	/** Total laureates born in this region across its countries. */
	laureates: number;
	countries: CountryListCountry[];
}
export interface CountryListData {
	meta: { n_countries: number; n_laureates: number; provenance: string; source: string };
	regions: CountryListRegion[];
}
export const countryListData = countryListRaw as unknown as CountryListData;

// ---------------------------------------------------------------------------
// laureate_links.json  (title-page scatter's laureate card)
//   Wikipedia link + Commons portrait per laureate, keyed by NobelRow.id.
//   Generated by scripts/laureate-links/laureate_links.py — site tooling, NOT a
//   replication output, so it is not synced by sync_to_site.py.
//   Loaded lazily (dynamic import → its own chunk) so the ~35 KB gzipped file
//   stays out of the title page's initial bundle; the scatter requests it the
//   first time a reader interacts with the chart.
// ---------------------------------------------------------------------------

/** Links for one laureate. Portrait fields are absent when Wikidata has none. */
export interface LaureateLink {
	/** English Wikipedia article. */
	wiki: string;
	/** Portrait thumbnail, hotlinked from Wikimedia's CDN (~250px wide). */
	img?: string;
	/** Photographer/author as plain text (Commons "Artist"), possibly shortened. */
	credit?: string;
	/** Licence short name, e.g. "CC BY-SA 4.0" or "Public domain". */
	license?: string;
	licenseUrl?: string;
	/** The image's Commons file page (full attribution and licence terms). */
	source?: string;
}

let laureateLinksPromise: Promise<Record<string, LaureateLink>> | null = null;

/** Fetch laureate links once; later calls share the same promise. A failed
 *  fetch (e.g. a network blip) is not cached, so the next call retries. */
export function loadLaureateLinks(): Promise<Record<string, LaureateLink>> {
	laureateLinksPromise ??= import('./laureate_links.json')
		.then((m) => (m.default as unknown as { laureates: Record<string, LaureateLink> }).laureates)
		.catch((err) => {
			laureateLinksPromise = null;
			throw err;
		});
	return laureateLinksPromise;
}
