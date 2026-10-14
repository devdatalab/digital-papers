#!/usr/bin/env python3
"""Rebuild every retained Nobel exhibit and check displayed exports; depends on package/code and generators.

Checks run against committed display exports and restore generated files afterward.
Manual published-table transcriptions are copied explicitly, not re-estimated.
"""
from pathlib import Path
from collections import Counter
import argparse
import csv
import json
import math
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
DISPLAY = ROOT.parent / 'data' if (ROOT.parent / 'data').exists() else ROOT / 'expected'
sys.path.insert(0, str(ROOT / 'package/code'))
from manifest import SCRIPTS


def differences(expected, actual, path=''):
    # Provenance locations and timestamps can change when a generator is relocated.
    if isinstance(expected, dict) and isinstance(actual, dict):
        result = []
        for key in sorted(set(expected) | set(actual)):
            if key in ('generated', 'source'):
                continue
            if key not in expected or key not in actual:
                result.append(f'{path}.{key}: missing key')
            else:
                result.extend(differences(expected[key], actual[key], f'{path}.{key}'))
        return result
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return [f'{path}: lengths differ ({len(expected)} vs {len(actual)})']
        return [difference for i, (a, b) in enumerate(zip(expected, actual)) for difference in differences(a, b, f'{path}[{i}]')]
    if isinstance(expected, (float, int)) and isinstance(actual, (float, int)):
        tolerance = 1e-7
        if path.startswith('.cells.') and '.fit.' in path:
            tolerance = {'intercept': 0.01, 'coef': 5e-6, 'se': 5e-6, 'p': 1e-5}.get(path.rsplit('.', 1)[-1], tolerance)
            if path.endswith('.p') and any((expected < cutoff) != (actual < cutoff) for cutoff in (0.1, 0.05, 0.01)):
                return [f'{path}: significance category changed']
        if math.isclose(expected, actual, rel_tol=1e-7, abs_tol=tolerance):
            return []
    return [] if expected == actual else [f'{path}: {expected!r} vs {actual!r}']


def extracted_inputs():
    rows = list(csv.DictReader((ROOT / 'package/data/nobelists_analysis.csv').open()))
    walkthrough = json.loads((ROOT / 'manual_data/rank_walkthrough.json').read_text())
    fields = {
        'fatherOccupation': 'father_occupation', 'occ1950Label': 'occ1950_label',
        'nationalIncomeRank': 'med_inctot_rank', 'globalIncomeRank': 'global_med_inctot_rank',
        'educationRank': 'educ_rank', 'prestigeRank': 'prestige_rank', 'gdpRatio': 'gdppc_ratio',
        'birthDecade': 'ipums_decade', 'country': 'country_name', 'category': 'category', 'prizeYear': 'prize_year'
    }
    for person in walkthrough['laureates']:
        matches = [row for row in rows if row['name'] == {'curie': 'Marie Curie, ne Sklodowska'}.get(person['id'], person['name']) and int(float(row['prize_year'])) == person['prizeYear']]
        if len(matches) != 1:
            raise ValueError(f'Expected one source row for {person["name"]}')
        row = matches[0]
        for field, column in fields.items():
            raw = row[column]
            person[field] = float(raw) if isinstance(person[field], (int, float)) else raw
        person['matchedDecade'] = int(row['ipums_decade_adjusted'][:4])
        person['usBorn'] = bool(int(float(row['usa'])))
    countries = json.loads((ROOT / 'manual_data/country_list.json').read_text())
    for region in countries['regions']:
        counts = Counter(row['country_name'] for row in rows if row['bloc'] == region['bloc'])
        region['countries'] = [dict(country=name, laureates=count) for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]
        region['laureates'] = sum(counts.values())
    countries['meta']['n_countries'] = len({row['country_name'] for row in rows})
    countries['meta']['n_laureates'] = len(rows)
    return {'rank_walkthrough.json': walkthrough, 'country_list.json': countries}


def run(check):
    snapshots = {path: path.read_bytes() for path in ROOT.rglob('*.json')}
    exports = {}
    failures = []
    try:
        for script in SCRIPTS:
            subprocess.run([sys.executable, str(script.path)], check=True, cwd=ROOT)
            for name in script.outputs:
                exports[name] = json.loads((script.output_dir / name).read_text())
        for name in ('extract_viz_data', 'extended_results', 'occ_rank_timeseries', 'occ_prize_shares'):
            folder = ROOT / 'generators' / name
            subprocess.run([sys.executable, str(folder / f'{name}.py')], check=True, cwd=ROOT)
            for path in (folder / 'output').glob('*.json'):
                exports[path.name] = json.loads(path.read_text())
        exports.update(extracted_inputs())
        for name in ('usa_vs_world_published', 'occupation_field_correspondence', 'laureate_links'):
            exports[name + '.json'] = json.loads((ROOT / 'manual_data' / (name + '.json')).read_text())
        for path in sorted(DISPLAY.glob('*.json')):
            if path.name not in exports:
                failures.append(f'{path.name}: no generator or declared input')
                continue
            if check:
                errors = differences(json.loads(path.read_text()), exports[path.name])
                if errors:
                    failures.extend(f'{path.name}{error}' for error in errors[:8])
                else:
                    print(f'PASS {path.name}')
            else:
                path.write_text(json.dumps(exports[path.name], ensure_ascii=False, indent=2) + '\n')
        if failures:
            raise SystemExit('\n'.join(['FAIL: displayed exports differ from regenerated data'] + failures))
        print('PASS: all displayed Nobel data is covered and reproduced')
    finally:
        if check:
            for path, content in snapshots.items():
                path.write_bytes(content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    run(parser.parse_args().check)
