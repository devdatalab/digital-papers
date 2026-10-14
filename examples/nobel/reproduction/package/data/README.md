# Data

Input datasets for the analysis scripts. **Read-only**: scripts never modify
them. `codebook.csv` lists every column of every file with its type, coverage,
an example value and (for key columns) a description.

| File | One row per | Rows | Contents |
| --- | --- | --- | --- |
| `nobelists_analysis.csv` | laureate | 735 | Main analysis file: prize, birth, country, father's occupation and its occ1950 code, occupation ranks, and derived variables. Input to almost every script. |
| `laureates_grounded_search.csv` | laureate | 735 | LLM-assisted web-search records supporting each father's occupation: occupation found, quote, reasoning, source URLs. Join to the analysis file on normalised name. |
| `occ1950_sci_field_classification.csv` | occupation | 113 | Scientific field of each occ1950 code (this is Table A13). |
| `ipums_parent_field_census_shared.csv` | occupation × decade × country | 22,176 | Census population share of each science-field occupation, for the countries and decades laureates come from. |
| `occ_rank_timeseries.csv` | occupation group × decade | 3,939 | US income and education ranks by occupation group, 1850–1970. |
| `microocc_census_shares.csv` | occupation group × decade | — | Complete U.S. occupation-group shares, 1850–1970, for the Figure A1 comparison. Detailed codes are summed within groups; each full decade is normalized to sum to one. |
| `occ_shares_occ1950_table.csv` | occupation | 269 | Laureate-father vs census shares and over-representation ratios. |
| `occ_shares_25group_table.csv` | occupation group | 24 | The same, in 25 groups. |
| `occ_shares_10group_table.csv` | occupation group | 10 | The same, in 10 broad groups. |

## Key variables

Socioeconomic status is measured by the **percentile rank of the father's
occupation**, computed within the laureate's country and census decade:

- `med_inctot_rank`: by median income (the paper's main measure)
- `educ_rank`: by education
- `global_med_inctot_rank`: against the global income distribution

All run from 0 to 100. See `codebook.csv` for everything else.

## Sources

Census-derived files (`ipums_parent_field_census_shared.csv`,
`occ_rank_timeseries.csv`, the `occ_shares_*` tables, and the rank columns of
`nobelists_analysis.csv`) are built from IPUMS census microdata. Cite IPUMS
as shown in ../README.md. Occupation labels (`father_occupation`,
`found_father_occ`) are normalised to sentence case, with spelling corrections.
