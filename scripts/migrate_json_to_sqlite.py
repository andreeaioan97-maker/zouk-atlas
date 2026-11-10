#!/usr/bin/env python3
"""One-time import of data/festivals.json into a new data/zouk_atlas.db.

  python3 -I scripts/migrate_json_to_sqlite.py [festivals.json] [out.db]

Refuses to overwrite an existing database.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import atlas_db

src = Path(sys.argv[1]) if len(sys.argv) > 1 else atlas_db.ROOT / 'data' / 'festivals.json'
out = Path(sys.argv[2]) if len(sys.argv) > 2 else atlas_db.DB
if out.exists():
    sys.exit(f'{out} already exists; not overwriting.')

data = json.load(open(src))
con = atlas_db.create(out)
con.execute('PRAGMA foreign_keys = ON')
for i, f in enumerate(data):
    con.execute('INSERT INTO series (id, name, city, country, style, website, instagram, facebook_page,'
                ' facebook_event_latest, last_checked, position) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                (f['id'], f['name'], f['city'], f['country'], f['style'], f['website'], f['instagram'],
                 f['facebook_page'], f['facebook_event_latest'], f['last_checked'], i + 1))
    for y, e in f['editions'].items():
        extra = set(e) - {'start', 'end', 'source', 'confirmed_by_organizer', 'city', 'country'}
        if extra:
            sys.exit(f'{f["id"]} {y}: unknown edition fields {extra}')
        c = e.get('confirmed_by_organizer')
        con.execute('INSERT INTO editions (series_id, year, start_date, end_date, source, confirmed_by_organizer,'
                    ' city, country) VALUES (?,?,?,?,?,?,?,?)',
                    (f['id'], int(y), e.get('start'), e.get('end'), e.get('source'),
                     None if c is None else int(bool(c)), e.get('city'), e.get('country')))
    con.execute('INSERT INTO year_status (series_id, year, status, note) VALUES (?,?,?,?)',
                (f['id'], 2027, f['status_2027'], f.get('note_2027')))
con.commit()
print(f'Imported {len(data)} series into {out}')
