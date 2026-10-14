#!/usr/bin/env python3
"""Rebuild every fictional exhibit from observations.csv; depends only on Python's standard library."""
from pathlib import Path
import argparse
import csv
import json
import statistics

ROOT = Path(__file__).resolve().parent


def make_results():
    rows = list(csv.DictReader((ROOT / 'observations.csv').open()))
    groups = []
    for name in sorted({row['group'] for row in rows}):
        selected = [row for row in rows if row['group'] == name]
        groups.append(dict(name=name, n=len(selected), outcome=statistics.mean(float(row['outcome']) for row in selected), hours=statistics.mean(float(row['hours']) for row in selected)))
    return dict(groups=groups)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = make_results()
    path = ROOT / 'results.json'
    if args.check:
        if result != json.loads(path.read_text()):
            raise SystemExit('FAIL: results differ from the displayed exhibit inputs')
        print('PASS: figure, table and sidebar reproduce exactly')
    else:
        path.write_text(json.dumps(result, indent=2) + '\n')
