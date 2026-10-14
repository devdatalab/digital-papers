/**
 * appendixTables — data-shaping layer for the appendix tables surfaced in the
 * right-hand "Additional Information" pane.
 *
 * Why this file exists:
 *   The appendix tables (occupation shares, subgroup trend slopes, regional
 *   top-percentile shares, gender robustness, occupation crosswalks) come from
 *   several differently-shaped replication JSONs. Rather than a bespoke Svelte
 *   component per table (the main-text pattern, justified there by six items),
 *   the ~7 appendix tables share one generic renderer, `AppendixTable.svelte`,
 *   and this module does the per-table data-shaping: it turns each typed dataset
 *   from `$nobel/data` into a uniform `AppendixTableSpec` (columns + grouped rows
 *   of pre-formatted cells). Keeping the shaping here (typed TS) separate from
 *   the rendering (Svelte) keeps both small and lets each table's column logic
 *   live in one place.
 *
 *   `getAppendixTable(id)` is the single entry point; `AppendixTable.svelte`
 *   calls it with the `table` string supplied by the content JSON.
 *
 * Upstream dependencies:
 *   $nobel/data (occShares10Data, occShares25Data, heteroTrendsData,
 *   regionalAnalysisData, genderAnalysisData, occupationListData,
 *   occShares1950ListData, countryListData, mainSpecData, mainRobustData)
 */
import {
	occShares10Data,
	occShares25Data,
	heteroTrendsData,
	regionalAnalysisData,
	genderAnalysisData,
	genderSpecRobustData,
	occupationListData,
	occShares1950ListData,
	countryListData,
	mainSpecData,
	mainRobustData,
	type OccShareGroupRow,
	type MainSpecRow,
	type RobustPanel,
	type RobustReg,
	type GenderRobustReg
} from '$nobel/data';
import { replicationSourceUrl } from '$lib/reading/replicationSource';
import usaVsWorldPublished from '$nobel/data/usa_vs_world_published.json';
import occupationFieldCorrespondence from '$nobel/data/occupation_field_correspondence.json';

/** A single table cell: `main` value with an optional `sub` line beneath it
 *  (used for the standard-error line under a coefficient). */
export interface TableCell {
	main: string;
	sub?: string;
}
export interface TableColumn {
	key: string;
	label: string;
	/** Left-align and wrap prose columns such as occupation names. */
	text?: boolean;
	/** Optional second header line (units, e.g. "share", "per 100 yrs"). */
	sublabel?: string;
}
export interface TableRow {
	label: string;
	cells: Record<string, TableCell | string>;
	/** Muted styling — for p-value / diagnostic rows that sit under a group. */
	muted?: boolean;
}
export interface TableGroup {
	/** Panel header spanning all columns; omit for an ungrouped block. */
	label?: string;
	rows: TableRow[];
}
export interface AppendixTableSpec {
	title: string;
	subtitle?: string;
	note: string;
	significanceLegend?: string;
	source: string;
	sourceUrl: string;
	/** Header for the left-most (row-label) column. */
	rowLabelHeader: string;
	columns: TableColumn[];
	groups: TableGroup[];
	/** Long reference tables get a capped-height vertical scroll region. */
	scrollY?: boolean;
	/** Smaller cell gutters and no minimum row-label width for sidebar tables. */
	compact?: boolean;
}

// ---------------------------------------------------------------------------
// Formatting helpers
// ---------------------------------------------------------------------------

/** Percent already on a 0–100 scale (e.g. laureate_pct). */
const pct1 = (v: number): string => `${v.toFixed(1)}%`;
/** Over-representation ratio. */
const ratio1 = (v: number): string => `${v.toFixed(1)}×`;

function stars(coef: number, se: number): string {
	if (se === 0) return '';
	const t = Math.abs(coef / se);
	if (t > 2.576) return '***';
	if (t > 1.96) return '**';
	if (t > 1.645) return '*';
	return '';
}

/** A coefficient reported per 100 prize years, with its SE on the sub line.
 *  `scale` converts the raw slope to display units (100 for per-100-years). */
function coefCell(coef: number, se: number, opts: { scale?: number; pct?: boolean; signed?: boolean } = {}): TableCell {
	const scale = opts.scale ?? 100;
	const v = coef * scale;
	const sev = se * scale;
	const digits = opts.pct ? 1 : 2;
	const sign = opts.signed && v > 0 ? '+' : '';
	const suffix = opts.pct ? '' : '';
	return {
		main: `${sign}${v.toFixed(digits)}${suffix}${stars(coef, se)}`,
		sub: `(${sev.toFixed(digits)})`
	};
}

/** A level estimate with its SE beneath. Two deliberate differences from
 *  `coefCell`:
 *   - No rescaling. The regression constant is a rank level at prize year 1901,
 *     not a slope, so the per-100-years convention doesn't apply to it.
 *   - No significance stars. Starring the constant only tests whether the fitted
 *     1901 rank differs from zero — a non-question for a rank near 92, and one a
 *     non-specialist could misread as a finding. The paper agrees in Tables A5
 *     and A6 (constant unstarred) but not in A7 (starred); we omit it in all
 *     three so the panels are at least consistent with each other. */
function levelCell(value: number, se: number): TableCell {
	return { main: value.toFixed(2), sub: `(${se.toFixed(2)})` };
}

function fmtP(p: number): string {
	if (p < 0.001) return '<0.001';
	return p.toFixed(3);
}

/** Narrow a `CoefSe | number` (or unknown nested value) to a coef/se pair. */
function asCoefSe(v: unknown): { coef: number; se: number } | null {
	if (v && typeof v === 'object' && 'coef' in v && 'se' in v) {
		const o = v as { coef: number; se: number };
		return { coef: o.coef, se: o.se };
	}
	return null;
}

// ---------------------------------------------------------------------------
// occ_shares_10 / occ_shares_25 — laureate vs. census occupation shares
// ---------------------------------------------------------------------------

function occSharesSpec(rows: OccShareGroupRow[], groups: 10 | 25): AppendixTableSpec {
	const sorted = [...rows].sort((a, b) => b.laureate_pct - a.laureate_pct);
	return {
		title: `Father occupation shares (${groups}-group)`,
		subtitle: 'Laureate fathers vs. the general population',
		rowLabelHeader: 'Occupation group',
		columns: [
			{ key: 'lau', label: 'Laureate', sublabel: 'share' },
			{ key: 'cen', label: 'Census', sublabel: 'share' },
			{ key: 'over', label: 'Over-rep.' }
		],
		groups: [
			{
				rows: sorted.map((r) => ({
					label: r.label,
					cells: {
						lau: pct1(r.laureate_pct),
						cen: pct1(r.census_pct),
						over: ratio1(r.overrep_ratio)
					}
				}))
			}
		],
		note: `Share of laureate fathers vs. their share of the working population in each of ${groups} occupation groups. Over-representation is the ratio of the two; values above 1× mean laureate fathers are more common in that group than in the population.`,
		source: 'occ_shares/occ_shares.py',
		sourceUrl: replicationSourceUrl('occ_shares/occ_shares.py')
	};
}

// ---------------------------------------------------------------------------
// hetero_trends — secular trend slopes by subgroup
// ---------------------------------------------------------------------------

const TREND_OUTCOMES = [
	{ key: 'med_inctot_rank', label: 'Natl. income', sub: 'rank' },
	{ key: 'educ_rank', label: 'Education', sub: 'rank' },
	{ key: 'global_med_inctot_rank', label: 'Global income', sub: 'rank' }
];

function trendCell(outcomeKey: string, panelKey: string, groupKey: string): TableCell | string {
	const outcome = heteroTrendsData.data[outcomeKey] as unknown as Record<
		string,
		Record<string, unknown>
	>;
	const slope = asCoefSe(outcome?.[panelKey]?.[groupKey]);
	if (!slope) return '—';
	return coefCell(slope.coef, slope.se);
}

function trendPRow(panelKey: string): TableRow {
	const cells: Record<string, TableCell | string> = {};
	for (const o of TREND_OUTCOMES) {
		const outcome = heteroTrendsData.data[o.key] as unknown as Record<string, Record<string, unknown>>;
		const p = outcome?.[panelKey]?.['p_equal'];
		cells[o.key] = typeof p === 'number' ? fmtP(p) : '';
	}
	return { label: 'p-value (equal)', cells, muted: true };
}

function heteroTrendsSpec(): AppendixTableSpec {
	const columns: TableColumn[] = TREND_OUTCOMES.map((o) => ({
		key: o.key,
		label: o.label,
		sublabel: o.sub
	}));
	const groupRow = (panel: string, key: string, label: string): TableRow => ({
		label,
		cells: Object.fromEntries(TREND_OUTCOMES.map((o) => [o.key, trendCell(o.key, panel, key)]))
	});

	return {
		title: 'Trend slopes by subgroup',
		subtitle: 'Change in father rank per 100 prize years',
		rowLabelHeader: 'Group',
		columns,
		groups: [
			{
				rows: [
					{
						label: 'All laureates',
						cells: Object.fromEntries(
							TREND_OUTCOMES.map((o) => {
								const s = heteroTrendsData.data[o.key]?.full_sample;
								return [o.key, s ? coefCell(s.coef, s.se) : '—'];
							})
						)
					}
				]
			},
			{
				label: 'A. Gender',
				rows: [
					groupRow('gender', 'male', 'Male'),
					groupRow('gender', 'female', 'Female'),
					trendPRow('gender')
				]
			},
			{
				label: 'B. Prize category',
				rows: [
					groupRow('category', 'chemistry', 'Chemistry'),
					groupRow('category', 'physics', 'Physics'),
					groupRow('category', 'medicine', 'Medicine'),
					groupRow('category', 'economics', 'Economics'),
					trendPRow('category')
				]
			},
			{
				label: 'C. Region',
				rows: [
					groupRow('region', 'usa', 'USA'),
					groupRow('region', 'western_europe', 'Western Europe'),
					groupRow('region', 'eastern_europe', 'Eastern Europe'),
					groupRow('region', 'global_south', 'Global South'),
					groupRow('region', 'other', 'Other'),
					trendPRow('region')
				]
			}
		],
		note: 'OLS slope of each rank outcome on prize year (× 100, i.e. rank points per 100 years), estimated separately within each subgroup. Robust standard errors in parentheses. The p-value row tests equality of slopes across groups in the panel. * p<0.10, ** p<0.05, *** p<0.01.',
		source: 'hetero_trends/hetero_trends.py',
		sourceUrl: replicationSourceUrl('hetero_trends/hetero_trends.py')
	};
}

// ---------------------------------------------------------------------------
// top_pctiles_usa — published Table A10: USA vs. rest of world
// ---------------------------------------------------------------------------

function topPctlSpec(): AppendixTableSpec {

	// The published paper uses N=714; current replication output uses N=713
	// and lacks the four indicator regressions. Preserve the published cells.
	return {
		title: usaVsWorldPublished.title,
		rowLabelHeader: 'Estimate',
		columns: usaVsWorldPublished.columns,
		groups: [{ rows: usaVsWorldPublished.rows }],
		significanceLegend: '* p<0.10, ** p<0.05, *** p<0.01.',
		note: usaVsWorldPublished.note,
		source: 'Published paper, Table A10 (May 2026)',
		sourceUrl: usaVsWorldPublished.meta.upstream
	};
}

// ---------------------------------------------------------------------------
// country_list — laureate birth countries by analysis region (A16)
// ---------------------------------------------------------------------------

/** The list of countries behind the West / East / Global South blocs used in the
 *  regional results. This publishes the regions the analysis actually uses — every
 *  laureate birth country with its bloc — rather than the paper's printed A11, a
 *  wider modern-country crosswalk that is not derivable from the analysis data
 *  (see docs/replication/unresolved_cross_references.md). Countries are grouped
 *  by bloc and ordered by laureate count, so the West's dominance is visible. */
function countryListSpec(): AppendixTableSpec {
	const { regions, meta } = countryListData;
	return {
		title: 'Countries in each region',
		rowLabelHeader: 'Country',
		columns: [{ key: 'n', label: 'Laureates' }],
		groups: regions.map((r) => ({
			label: `${r.label} — ${r.countries.length} countries, ${r.laureates} laureates`,
			rows: r.countries.map((c) => ({ label: c.country, cells: { n: String(c.laureates) } }))
		})),
		note: `The world regions used in the regional results (Table 2 and the regional appendix), listing every laureate birth country with its bloc and the number of laureates (of ${meta.n_laureates}) born there.`,
		source: 'regional_analysis/regional_analysis.py',
		sourceUrl: replicationSourceUrl('regional_analysis/regional_analysis.py'),
		scrollY: true
	};
}

// ---------------------------------------------------------------------------
// gender_robust — secular trends and slope-equality tests by gender
// ---------------------------------------------------------------------------

function genderRobustSpec(): AppendixTableSpec {
	const gs = genderAnalysisData.data.gender_spec;
	const slopeTests = genderAnalysisData.data.slope_tests;
	const outcomes = [
		{ specKey: 'med_inctot_rank', label: 'Natl. income rank' },
		{ specKey: 'educ_rank', label: 'Education rank' },
		{ specKey: 'global_med_inctot_rank', label: 'Global income rank' }
	];

	const rows: TableRow[] = outcomes.map((o) => {
		const cell = gs?.[o.specKey];
		const male = cell?.male?.prize_year_rescaled;
		const female = cell?.female?.prize_year_rescaled;
		const test = slopeTests?.[o.specKey];
		return {
			label: o.label,
			cells: {
				male: male ? coefCell(male.coef, male.se) : '—',
				female: female ? coefCell(female.coef, female.se) : '—',
				pDifference: test ? fmtP(test.p_equal_slopes) : '—'
			}
		};
	});

	return {
		title: 'Secular trend in father rank, by gender',
		rowLabelHeader: 'Outcome',
		columns: [
			{ key: 'male', label: 'Male', sublabel: 'trend/100yr' },
			{ key: 'female', label: 'Female', sublabel: 'trend/100yr' },
			{ key: 'pDifference', label: 'Slope difference', sublabel: 'p-value' }
		],
		groups: [{ rows }],
		note: 'Estimates are from OLS regressions of father rank on prize year (×100). * p<0.10, ** p<0.05, *** p<0.01.',
		source: 'gender_analysis/gender_analysis.py',
		sourceUrl: replicationSourceUrl('gender_analysis/gender_analysis.py')
	};
}

// ---------------------------------------------------------------------------
// gender_spec_robust — the gender gap under four exclusion samples
// (the paper's Appendix Table A8; surfaced here as panel A3)
// ---------------------------------------------------------------------------

/** The four exclusion samples, columns of the gap matrix, in the paper's panel
 *  order. Labels are kept short for the narrow right-hand pane. */
const GSR_SAMPLES = [
	{ key: 'A', label: 'Excl. difficult' },
	{ key: 'B', label: 'Excl. aristocrats' },
	{ key: 'C', label: 'Excl. owners' },
	{ key: 'D', label: 'Excl. economics' }
];

/** p-value significance markers, matching the published table's convention. */
function starsFromP(p: number): string {
	if (p < 0.01) return '***';
	if (p < 0.05) return '**';
	if (p < 0.1) return '*';
	return '';
}

/** One gap cell: the female coefficient (female − male baseline) with a leading
 *  `+` on positive gaps and the HC1 SE beneath. `withStars` is true only for the
 *  four Top-N indicator outcomes — the paper leaves the two continuous
 *  "Average Rank" rows unstarred even where they are significant, so the panel
 *  follows suit (the p-values live in the JSON regardless). */
function gsrGapCell(reg: GenderRobustReg, digits: number, withStars: boolean): TableCell {
	const sign = reg.coef > 0 ? '+' : '';
	const star = withStars ? starsFromP(reg.p) : '';
	return {
		main: `${sign}${reg.coef.toFixed(digits)}${star}`,
		sub: `(${reg.se.toFixed(digits)})`
	};
}

function genderSpecRobustSpec(): AppendixTableSpec {
	const panels = genderSpecRobustData.data;
	const columns: TableColumn[] = GSR_SAMPLES.map((s) => ({
		key: s.key,
		label: s.label,
		sublabel: `n=${panels[s.key]?.n ?? '—'}`
	}));

	// Each row is one outcome across the four samples; `digits`/`withStars` follow
	// the outcome type (continuous rank vs. indicator share).
	const outcomeRow = (
		label: string,
		outcomeKey: string,
		digits: number,
		withStars: boolean
	): TableRow => ({
		label,
		cells: Object.fromEntries(
			GSR_SAMPLES.map((s) => {
				const reg = panels[s.key]?.outcomes[outcomeKey];
				return [s.key, reg ? gsrGapCell(reg, digits, withStars) : '—'];
			})
		)
	});

	return {
		title: 'The gender gap, under four robustness samples',
		subtitle: 'Male–female difference in father’s rank, dropping the hardest-to-place fathers',
		rowLabelHeader: 'Outcome',
		columns,
		groups: [
			{
				label: 'Average rank',
				rows: [
					outcomeRow('Income', 'med_inctot_rank', 2, false),
					outcomeRow('Education', 'educ_rank', 2, false)
				]
			},
			{
				label: 'Top 10% family',
				rows: [
					outcomeRow('Income', 'top_decile_med_inctot', 3, true),
					outcomeRow('Education', 'top_decile_educ', 3, true)
				]
			},
			{
				label: 'Top 20% family',
				rows: [
					outcomeRow('Income', 'top_20pct_med_inctot', 3, true),
					outcomeRow('Education', 'top_20pct_educ', 3, true)
				]
			}
		],
		note: 'Each cell shows the female-minus-male outcome difference, from four samples that each test robustness to dropping a subset of laureate fathers. Difficult-to-rank fathers are fathers whose occupation was vaguely specified or difficult to match to a census category. A positive number means female laureates had higher-SES fathers. Robust standard errors in parentheses. * p<0.10, ** p<0.05, *** p<0.01.',
		source: 'gender_spec_robust/gender_spec_robust.py',
		sourceUrl: replicationSourceUrl('gender_spec_robust/gender_spec_robust.py')
	};
}

// ---------------------------------------------------------------------------
// occ_freq — occupation → group crosswalk (reference)
// ---------------------------------------------------------------------------

function occFreqSpec(): AppendixTableSpec {
	const entries = Object.values(occupationListData.data).sort((a, b) => a.label.localeCompare(b.label));
	return {
		title: 'Occupation → group crosswalk',
		subtitle: `How each of ${entries.length} detailed occupations maps to the coarse groups`,
		rowLabelHeader: 'Occupation',
		columns: [
			{ key: 'g10', label: '10-group' },
			{ key: 'g25', label: '25-group' }
		],
		groups: [
			{
				rows: entries.map((e) => ({
					label: e.label,
					cells: { g10: e.group_10, g25: e.group_25 }
				}))
			}
		],
		note: 'Correspondence between each detailed (occ1950) occupation and the 10- and 25-group aggregations used in the occupation-share tables.',
		source: 'occ_shares/occ_shares.py',
		sourceUrl: replicationSourceUrl('occ_shares/occ_shares.py'),
		scrollY: true
	};
}

// ---------------------------------------------------------------------------
// occ1950_correspondence — full occ1950 share table (reference)
// ---------------------------------------------------------------------------

function occ1950Spec(): AppendixTableSpec {
	const rows = [...occShares1950ListData.data].sort((a, b) => b.laureate_n - a.laureate_n);
	return {
		title: 'Father occupations in detail (occ1950)',
		subtitle: `Laureate vs. census share for all ${rows.length} detailed occupations`,
		rowLabelHeader: 'Occupation',
		columns: [
			{ key: 'g10', label: 'Group' },
			{ key: 'lau', label: 'Laur.', sublabel: 'share' },
			{ key: 'cen', label: 'Cens.', sublabel: 'share' },
			{ key: 'over', label: 'O-rep.' }
		],
		groups: [
			{
				rows: rows.map((r) => ({
					label: r.label,
					cells: {
						g10: r.group_10,
						lau: pct1(r.laureate_pct),
						cen: pct1(r.census_pct),
						over: r.overrep_ratio > 0 ? ratio1(r.overrep_ratio) : '—'
					}
				}))
			}
		],
		note: 'Every detailed (occ1950) father occupation with its 10-group label, its share among laureate fathers, its share of the working population, and the over-representation ratio. Sorted by number of laureates.',
		source: 'occ_shares/occ_shares.py',
		sourceUrl: replicationSourceUrl('occ_shares/occ_shares.py'),
		scrollY: true
	};
}

// ---------------------------------------------------------------------------
// occ1950_parent_field_correspondence — published occupation-to-field mapping
// ---------------------------------------------------------------------------

function occupationFieldSpec(): AppendixTableSpec {

	// Stack the paper's two sets of columns into one four-column table, keeping
	// its panel order, occupation labels, counts, and scientific-field assignments.
	return {
		title: 'Occupation-field correspondence',
		rowLabelHeader: 'Code',
		columns: [
			{ key: 'occupation', label: 'Occupation', text: true },
			{ key: 'n', label: 'N' },
			{ key: 'field', label: 'Field', text: true }
		],
		groups: occupationFieldCorrespondence.groups.map((group) => ({
			label: group.label,
			rows: group.rows.map((row) => ({
				label: String(row.code),
				cells: { occupation: row.occupation, n: String(row.n), field: row.field }
			}))
		})),
		note: '',
		source: 'Published paper, Table A13',
		sourceUrl: occupationFieldCorrespondence.meta.upstream,
		scrollY: true,
		compact: true
	};
}

// ---------------------------------------------------------------------------
// pregdp — global rank with and without the country-GDP adjustment
// (the paper's Appendix Table A7; surfaced here as panel A14)
// ---------------------------------------------------------------------------

function pregdpSpec(): AppendixTableSpec {
	// Both columns come from the Table 1 generator, which already runs this
	// specification on the adjusted and unadjusted global rank.
	const cols = [
		{ key: 'orig', row: mainSpecData.data.global_med_inctot_rank },
		{ key: 'noadj', row: mainSpecData.data.global_med_inctot_pregdp_rank }
	];
	const row = (label: string, fn: (r: MainSpecRow) => TableCell | string): TableRow => ({
		label,
		cells: Object.fromEntries(cols.map((c) => [c.key, fn(c.row)]))
	});

	return {
		title: 'Global rank, with and without the GDP adjustment',
		subtitle: 'Does adjusting for country income drive the global-rank result?',
		rowLabelHeader: 'Estimate',
		columns: [
			{ key: 'orig', label: 'Original', sublabel: 'global rank' },
			{ key: 'noadj', label: 'No adjustment', sublabel: 'global rank' }
		],
		groups: [
			{
				rows: [
					row('Constant (1901)', (r) => levelCell(r.intercept, r.intercept_se)),
					row('Trend (per 100 years)', (r) => coefCell(r.coef, r.se)),
					row('Observations', (r) => String(r.n)),
					row('R²', (r) => r.r2.toFixed(3))
				]
			}
		],
		note: "The table shows estimates from a regression of laureate global ranking on a constant and on the number of years since the first Nobel Prize in 1901. Column 1 corresponds to the primary estimates displayed in Panel C of Figure 2. In Column 2, global income ranks are calculated without adjusting national occupation rank distributions for country GDP level. Standard errors are in parentheses.",
		source: 'main_spec/main_spec.py',
		sourceUrl: replicationSourceUrl('main_spec/main_spec.py')
	};
}

// ---------------------------------------------------------------------------
// main_robust / main_robust_2 — the Table 1 trend under alternate samples and
// codings (the paper's Appendix Tables A5/A6; surfaced here as panels A2/A13)
// ---------------------------------------------------------------------------

const ROBUST_COLUMNS: TableColumn[] = [
	{ key: 'inc', label: 'National income', sublabel: 'rank' },
	{ key: 'edu', label: 'National education', sublabel: 'rank' }
];

/** The three rows every robustness panel shows. Trend `stars` come from the
 *  generator (computed from exact p-values and verified cell-by-cell against the
 *  published table) rather than being re-derived here. */
function robustRows(panel: RobustPanel): TableRow[] {
	// Panels that recode education only carry no `income` key; the published
	// table leaves those cells blank.
	const of = (fn: (r: RobustReg) => TableCell | string): Record<string, TableCell | string> => ({
		inc: panel.income ? fn(panel.income) : '—',
		edu: fn(panel.education)
	});
	return [
		{
			label: 'Constant (1901)',
			cells: of((r) => levelCell(r.constant, r.constant_se))
		},
		{
			label: 'Trend (per 100 years)',
			cells: of((r) => ({
				main: `${(r.coef * 100).toFixed(2)}${r.stars}`,
				sub: `(${(r.se * 100).toFixed(2)})`
			}))
		},
		{ label: 'Observations', cells: of((r) => String(r.n)), muted: true }
	];
}

function mainRobustSpec(which: 'a5' | 'a6'): AppendixTableSpec {
	const groups: TableGroup[] = Object.entries(mainRobustData.data[which]).map(([key, panel]) => ({
		label: `${key}. ${panel.title}`,
		rows: robustRows(panel)
	}));

	if (which === 'a5') {
		return {
			title: 'Robustness to sample restrictions',
			subtitle: 'The headline trend, re-estimated on four alternate samples',
			rowLabelHeader: 'Estimate',
			columns: ROBUST_COLUMNS,
			groups,
			note: "The table shows estimates from an OLS regression of Nobel laureate father SES rank on a linear time trend. These specifications are based on the primary specification in Table 1, with the following modifications. In Panel A, we exclude 13 laureates whose father occupations were vaguely described and difficult to classify. In Panel B, we exclude 8 laureates whose fathers were aristocrats (who were classified as being at education and income percentile 100 in the main analysis). In Panel C, we exclude 134 children of business owners and farmers, since these occupations can be associated with a wide range of possible SES ranks. In Panel D, we exclude the Nobel Prize in economics.",
			source: 'main_robust/main_robust.py',
			sourceUrl: replicationSourceUrl('main_robust/main_robust.py')
		};
	}
	return {
		title: 'Robustness to alternate codings',
		subtitle: 'The headline trend, re-estimated with alternate rank codings',
		rowLabelHeader: 'Estimate',
		columns: ROBUST_COLUMNS,
		groups,
		note: "The table shows estimates from an OLS regression of Nobel laureate father SES rank on a linear time trend. These specifications are based on the primary specification in Table 1, with the following modifications. In Panel A, we classified business owners as small, medium or large. For small business owners, we used the 25th percentile education and income data from the Census to calculate the father's rank. For large business owners, we used the 75th. In Panel B, we override the father's education rank in cases where the historical record documents the actual education level of the father. In Panel C, we do both.",
		source: 'main_robust/main_robust.py',
		sourceUrl: replicationSourceUrl('main_robust/main_robust.py')
	};
}

// ---------------------------------------------------------------------------
// Registry
// ---------------------------------------------------------------------------

/** Resolve a table id (supplied by the content JSON's component block) to its
 *  fully-shaped spec, or `null` if unknown. */
export function getAppendixTable(id: string): AppendixTableSpec | null {
	switch (id) {
		case 'occ_shares_10':
			return occSharesSpec(occShares10Data.data, 10);
		case 'occ_shares_25':
			return occSharesSpec(occShares25Data.data, 25);
		case 'hetero_trends':
			return heteroTrendsSpec();
		case 'top_pctiles_usa':
			return topPctlSpec();
		case 'country_list':
			return countryListSpec();
		case 'gender_robust':
			return genderRobustSpec();
		case 'gender_spec_robust':
			return genderSpecRobustSpec();
		case 'occ_freq':
			return occFreqSpec();
		case 'occ1950_correspondence':
			return occ1950Spec();
		case 'occ1950_parent_field_correspondence':
			return occupationFieldSpec();
		// Ids below name the paper's table (`tab:*` labels in the prose), not the
		// panel number they appear under — the site's A-numbering is its own
		// sequence and does not track the paper's.
		case 'pregdp':
			return pregdpSpec();
		case 'main_robust':
			return mainRobustSpec('a5');
		case 'main_robust_2':
			return mainRobustSpec('a6');
		default:
			return null;
	}
}
