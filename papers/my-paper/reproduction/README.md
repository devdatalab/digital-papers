<!-- Independent reproduction instructions for fictional example exhibits. -->
# Reproduce the fictional paper

Requires Python 3.11+ and its standard library only.

```sh
python make_all.py --check
python make_all.py
```

The first command verifies the shipped results; the second regenerates them.
`observations.csv` contains nine fictional observations. `make_all.py` calculates
arithmetic group means and writes `results.json`. The main figure, table, and sidebar
all render that export. Captions and notes describe the same calculations.

Only the supplied fictional example prose and fictional observations are CC0;
`make_all.py` and its technical documentation are MIT. No real study is represented.
These grants do not extend to real manuscript text, captions, notes, paper-specific
explanations or research inputs and outputs added when adapting this bundle. Preserve
existing third-party licenses and specify any new code/data grants separately.

See [COPYRIGHT.md](COPYRIGHT.md) for the research-content reservation that travels
with this bundle. Update these notices when replacing the fictional inputs.
