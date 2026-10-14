<!-- Independent entry point for all retained Nobel calculations and explicit manual inputs. -->
# Reproduce the Nobel teaching example

This bundle works without the website or a private research checkout. Use Python 3.11+
and install the numerical dependencies in a virtual environment:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python make_all.py --check
```

`--check` recalculates the analysis and explorer data and compares it with `expected/`.
It restores generated package outputs after checking. Without `--check`, the runner
regenerates the exports. In the website checkout the exports are in `../data/`; an
independent extracted bundle uses its own `expected/` folder.

`package/code/manifest.py` lists the retained analysis scripts. The four `generators/`
folders produce scatter/raw-explorer, extended-results, occupation-rank and occupation-share
exports. They run after analysis, since occupation shares use analysis outputs.
`make_all.py` additionally extracts sidebar walkthrough values and country counts from the
analysis CSV. The five-row raw explorer is a presentation subset; the analysis CSV remains full.

## Declared source inputs

`manual_data/rank_walkthrough.json` specifies the six illustrative people and display labels;
numerical values are extracted from the analysis CSV and checked. `country_list.json` defines
region ordering and labels; country counts are rebuilt from the CSV.

`usa_vs_world_published.json` and `occupation_field_correspondence.json` are preserved manual
transcriptions of published PDF tables, with provenance. They are copied and verified, not
re-estimated. The published USA/world table intentionally differs from the current regression
output. `laureate_links.json` is an external-service portrait/link catalogue, also a declared
input rather than a scientific calculation. Images are externally linked with credit metadata.

The bundle's research licenses and data interpretation notes remain in
`package/LICENSE.md`, `package/CITATION.cff`, and `package/data/README.md`.
The website's framework license does not relicense the paper text or research inputs.

## Numerical comparison

Most numeric values use absolute/relative tolerance `1e-7`. Extended-results subgroup
fits use the inherited uncentered-year OLS implementation, which inverts X′X and is
sensitive to numerical-library differences. Its stored intercepts are compared within
0.01, slopes and standard errors within 0.000005, and p-values within 0.00001. Significance
categories at 10%, 5%, and 1% must stay identical. Counts, histogram bins and trend points
still use the strict comparison. Displayed exports are preserved, not replaced during checks.
