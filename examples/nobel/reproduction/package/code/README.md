<!-- Explain the retained analysis scripts without the removed full-package runner. -->
# Retained analysis

`manifest.py` lists the analysis scripts used by the teaching excerpt. Each reads
`../data/` and writes JSON to its own `output/` folder. The single reproduction entry
point is `../../make_all.py`; it also rebuilds the explorer exports and compares the
results with what the example displays. The Python scripts are ports of the authors'
original Stata calculations; original-file names in comments record provenance.
