#!/usr/bin/env python3
"""Verify source fidelity, example registrations, and public-file hygiene; depends only on committed examples."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
errors = []


def atoms(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ('text', 'caption', 'title', 'question', 'attribution', 'subtitle') and isinstance(item, str):
                yield item
            elif isinstance(item, (dict, list)):
                yield from atoms(item)
    elif isinstance(value, list):
        for item in value:
            yield from atoms(item)


for forbidden in ('agents-paul', 'agents-paul.md', 'ref-reports', 'pipeline', '.env'):
    if (ROOT / forbidden).exists():
        errors.append(f'Private/legacy path remains: {forbidden}')

nobel = ROOT / 'examples/nobel'
source_inventory = []
for path in sorted((nobel / 'content/sections').glob('*.json')):
    content = json.loads(path.read_text())
    if content['id'] == 'referee-comments-and-responses':
        continue
    source_path = nobel / 'source/sections' / path.name
    source = json.loads(source_path.read_text())
    source_atoms = set(atoms(source))
    for text in atoms(content):
        if text.startswith('[Example excerpt:') or text == ' Read the complete digital publication.':
            continue
        if text not in source_atoms:
            errors.append(f'Source wording changed: {path.relative_to(ROOT)}')
    source_inventory.append(dict(section=content['id'], source=str(source_path.relative_to(nobel)), sha256=hashlib.sha256(source_path.read_bytes()).hexdigest()))

submissions = json.loads((nobel / 'content/referee-submissions.json').read_text())['submissions']
if [submission['journal'] for submission in submissions] != ['Science', 'Nature', 'Quarterly Journal of Economics']:
    errors.append('Expected the first three journal labels')
for submission in submissions:
    if submission['manuscriptUrl'] or submission['submissionDate'] or submission['responseDate']:
        errors.append('Actual submission metadata remains')
    for key in ('preamble', 'editor', 'response'):
        if not submission[key].startswith('['):
            errors.append(f'Actual correspondence remains in {key}')

# Inspect only distributable source folders; ignore dependencies and generated output.
patterns = [re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)'), re.compile(r'https://(?:drive|docs)\.google\.com/'), re.compile(r'/Users/[^/\s]+/')]
for folder in ('src', 'examples', 'papers', 'scripts', 'docs', '.github'):
    for path in (ROOT / folder).rglob('*'):
        if not path.is_file() or path.suffix.lower() not in ('.ts', '.js', '.mjs', '.svelte', '.json', '.csv', '.md', '.py', '.yml', '.txt'):
            continue
        if any(part in ('__pycache__', '.venv') for part in path.parts):
            continue
        content = path.read_text(errors='replace')
        if path == Path(__file__).resolve():
            continue
        if any(pattern.search(content) for pattern in patterns):
            errors.append(f'Potential private reference in {path.relative_to(ROOT)}')

# Every figure label and annotation module must have an active registration.
for paper in (ROOT / 'examples/minimal', nobel, ROOT / 'papers/my-paper'):
    registration = (paper / 'exhibits/index.ts').read_text()
    if paper == nobel:
        registration += (paper / 'exhibits/appendixRegistry.ts').read_text()
    def blocks(values):
        for block in values:
            if block['type'] in ('figure', 'table') and not block.get('source') and block.get('label') not in registration:
                errors.append(f'Unregistered exhibit in {paper.relative_to(ROOT)}: {block.get("label")}')
            if block['type'] == 'collapsible':
                blocks(block['blocks'])
            if block['type'] == 'faq':
                for item in block['items']:
                    blocks(item['blocks'])
    for path in (paper / 'content/sections').glob('*.json'):
        section = json.loads(path.read_text())
        blocks(section['blocks'])
        for annotation in section.get('annotations', []):
            for block in annotation['body']:
                if block['type'] == 'component' and block['component'] not in registration:
                    errors.append(f'Unregistered panel: {block["component"]}')
                if block['type'] == 'image' and not block['src'].startswith('http') and not (paper / 'assets' / block['src']).exists():
                    errors.append(f'Missing annotation image: {block["src"]}')

if errors:
    raise SystemExit('\n'.join(['FAIL'] + sorted(set(errors))))
print(f'PASS: original wording retained in {len(source_inventory)} Nobel sections; all examples registered; public-file audit clear')
