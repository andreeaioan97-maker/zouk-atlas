#!/usr/bin/env python3
"""Build the Zouk Atlas 2027 page from the database.

  python3 -I scripts/build_page.py scripts/page/template.html build/zouk-atlas-2027.html
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import atlas_db

tpl, out = sys.argv[1:3]
d = atlas_db.load_festivals()
rows, asof = [], max(f.get('last_checked') or '' for f in d)
for f in d:
    e = f['editions']
    prev = [e[y] for y in sorted(e) if y < '2027' and e[y].get('start')]
    rows.append({k: f.get(k) for k in ('name', 'city', 'country', 'style', 'website', 'instagram')} | {
        'status': f['status_2027'], 'note': f.get('note_2027'),
        'e27': e.get('2027'), 'last': prev[-1] if prev else None})
html = open(tpl).read().replace('/*DATA*/[]', json.dumps(rows, ensure_ascii=False).replace('</', '<\\/')).replace('/*ASOF*/', asof)
Path(out).parent.mkdir(parents=True, exist_ok=True)
Path(out).write_text(html)
print(len(rows), asof, len(html))
