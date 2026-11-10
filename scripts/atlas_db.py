"""Shared access to the Zouk Atlas SQLite database (data/zouk_atlas.db)."""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / 'data' / 'zouk_atlas.db'
SCHEMA = ROOT / 'data' / 'schema.sql'
STATUS_YEAR = 2027   # the year the list currently tracks (status_2027 / note_2027 in exports)


def connect(path=DB):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    return con


def create(path=DB):
    con = sqlite3.connect(path)
    con.executescript(SCHEMA.read_text())
    con.commit()
    return con


def load_festivals(con=None):
    """Return every series as a dict in the festivals.json export shape."""
    con = con or connect()
    eds = {}
    for e in con.execute('SELECT * FROM editions ORDER BY series_id, year'):
        d = {'start': e['start_date'], 'end': e['end_date'], 'source': e['source']}
        if e['confirmed_by_organizer'] is not None:
            d['confirmed_by_organizer'] = bool(e['confirmed_by_organizer'])
        for k in ('city', 'country'):
            if e[k] is not None:
                d[k] = e[k]
        eds.setdefault(e['series_id'], {})[str(e['year'])] = d
    st = {r['series_id']: r for r in con.execute('SELECT * FROM year_status WHERE year = ?', (STATUS_YEAR,))}
    out = []
    for s in con.execute('SELECT * FROM series ORDER BY position'):
        y = st.get(s['id'])
        f = {'id': s['id'], 'name': s['name'], 'city': s['city'], 'country': s['country'], 'style': s['style'],
             'editions': eds.get(s['id'], {}),
             f'status_{STATUS_YEAR}': y['status'] if y else None,
             'website': s['website'], 'facebook_event_latest': s['facebook_event_latest'],
             'facebook_page': s['facebook_page'], 'instagram': s['instagram'], 'last_checked': s['last_checked']}
        if y and y['note'] is not None:
            f[f'note_{STATUS_YEAR}'] = y['note']
        out.append(f)
    return out
