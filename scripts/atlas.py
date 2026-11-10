#!/usr/bin/env python3
"""Edit and export the Zouk Atlas database (data/zouk_atlas.db).

  python3 -I scripts/atlas.py show ID
  python3 -I scripts/atlas.py set-edition ID YEAR --start D --end D --source URL [--confirmed | --not-confirmed]
                                          [--city C --country C] [--keep-status]
  python3 -I scripts/atlas.py set-status ID YEAR STATUS [--note TEXT]
  python3 -I scripts/atlas.py set-note ID YEAR TEXT
  python3 -I scripts/atlas.py touch ID [ID ...] [--date YYYY-MM-DD]
  python3 -I scripts/atlas.py add-series --id ID --name N --city C --country C --style S [--status S --note T]
                                         [--website U --instagram U --facebook-page U --facebook-event U]
  python3 -I scripts/atlas.py export          # writes data/festivals.json and data/festivals.csv
  python3 -I scripts/atlas.py counts [--year 2027]

set-edition also marks that year's status as "listed" unless --keep-status is given.
"""
import argparse, csv, datetime, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import atlas_db

DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def date(s):
    if s is not None and not DATE.match(s):
        raise argparse.ArgumentTypeError(f'expected YYYY-MM-DD, got {s!r}')
    datetime.date.fromisoformat(s)
    return s


def need(con, sid):
    if not con.execute('SELECT 1 FROM series WHERE id = ?', (sid,)).fetchone():
        sys.exit(f'No series with id {sid!r}')


def export(con):
    data = atlas_db.load_festivals(con)
    j = atlas_db.ROOT / 'data' / 'festivals.json'
    j.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    with open(atlas_db.ROOT / 'data' / 'festivals.csv', 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['name', 'city', 'country', 'style', '2025', '2026', '2027', 'status_2027', 'website', 'instagram',
                    'facebook_page', 'facebook_event_latest', 'sources'])
        for f in data:
            e = f['editions']
            g = lambda y: '' if y not in e else ('?' if not e[y].get('start') else (
                e[y]['start'] if not e[y].get('end') else f"{e[y]['start']} → {e[y]['end']}"))
            w.writerow([f['name'], f['city'], f['country'], f['style'], g('2025'), g('2026'), g('2027'),
                        f['status_2027'], f['website'] or '', f['instagram'] or '', f['facebook_page'] or '',
                        f['facebook_event_latest'] or '', ' '.join(e[y]['source'] for y in sorted(e))])
    print(f'Exported {len(data)} series to data/festivals.json and data/festivals.csv')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('show'); p.add_argument('id')
    p = sub.add_parser('set-edition'); p.add_argument('id'); p.add_argument('year', type=int)
    p.add_argument('--start', type=date, required=True); p.add_argument('--end', type=date)
    p.add_argument('--source', required=True)
    g = p.add_mutually_exclusive_group(); g.add_argument('--confirmed', action='store_true'); g.add_argument('--not-confirmed', action='store_true')
    p.add_argument('--city'); p.add_argument('--country'); p.add_argument('--keep-status', action='store_true')
    p = sub.add_parser('set-status'); p.add_argument('id'); p.add_argument('year', type=int); p.add_argument('status'); p.add_argument('--note')
    p = sub.add_parser('set-note'); p.add_argument('id'); p.add_argument('year', type=int); p.add_argument('note')
    p = sub.add_parser('touch'); p.add_argument('ids', nargs='+'); p.add_argument('--date', type=date, default=datetime.date.today().isoformat())
    p = sub.add_parser('add-series')
    for k in ('id', 'name', 'city', 'country'):
        p.add_argument('--' + k, required=True)
    p.add_argument('--style', required=True, choices=['bz', 'bz+lambada', 'lambada', 'mixed', 'bachazouk'])
    for k in ('website', 'instagram', 'facebook-page', 'facebook-event'):
        p.add_argument('--' + k)
    p.add_argument('--status', default='expected'); p.add_argument('--note')
    sub.add_parser('export')
    p = sub.add_parser('counts'); p.add_argument('--year', type=int, default=atlas_db.STATUS_YEAR)
    a = ap.parse_args()

    con = atlas_db.connect()
    if a.cmd == 'show':
        need(con, a.id)
        print(json.dumps(next(f for f in atlas_db.load_festivals(con) if f['id'] == a.id), ensure_ascii=False, indent=2))
    elif a.cmd == 'set-edition':
        need(con, a.id)
        if a.end and a.end < a.start:
            sys.exit('--end is before --start')
        conf = 1 if a.confirmed else 0 if a.not_confirmed else None
        con.execute('INSERT INTO editions (series_id, year, start_date, end_date, source, confirmed_by_organizer, city, country)'
                    ' VALUES (?,?,?,?,?,?,?,?) ON CONFLICT (series_id, year) DO UPDATE SET start_date=excluded.start_date,'
                    ' end_date=excluded.end_date, source=excluded.source, confirmed_by_organizer=excluded.confirmed_by_organizer,'
                    ' city=excluded.city, country=excluded.country',
                    (a.id, a.year, a.start, a.end, a.source, conf, a.city, a.country))
        if not a.keep_status:
            con.execute('INSERT INTO year_status (series_id, year, status) VALUES (?,?,?) ON CONFLICT (series_id, year)'
                        ' DO UPDATE SET status=excluded.status', (a.id, a.year, 'listed'))
    elif a.cmd == 'set-status':
        need(con, a.id)
        con.execute('INSERT INTO year_status (series_id, year, status, note) VALUES (?,?,?,?) ON CONFLICT (series_id, year)'
                    ' DO UPDATE SET status=excluded.status, note=COALESCE(excluded.note, note)', (a.id, a.year, a.status, a.note))
    elif a.cmd == 'set-note':
        need(con, a.id)
        cur = con.execute('UPDATE year_status SET note = ? WHERE series_id = ? AND year = ?', (a.note, a.id, a.year))
        if not cur.rowcount:
            sys.exit(f'{a.id} has no status for {a.year}; use set-status first')
    elif a.cmd == 'touch':
        for i in a.ids:
            need(con, i)
        con.executemany('UPDATE series SET last_checked = ? WHERE id = ?', [(a.date, i) for i in a.ids])
    elif a.cmd == 'add-series':
        if con.execute('SELECT 1 FROM series WHERE id = ?', (a.id,)).fetchone():
            sys.exit(f'Series {a.id!r} already exists')
        pos = con.execute('SELECT COALESCE(MAX(position), 0) + 1 FROM series').fetchone()[0]
        con.execute('INSERT INTO series (id, name, city, country, style, website, instagram, facebook_page, facebook_event_latest,'
                    ' last_checked, position) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                    (a.id, a.name, a.city, a.country, a.style, a.website, a.instagram, a.facebook_page, a.facebook_event,
                     datetime.date.today().isoformat(), pos))
        con.execute('INSERT INTO year_status (series_id, year, status, note) VALUES (?,?,?,?)',
                    (a.id, atlas_db.STATUS_YEAR, a.status, a.note))
    elif a.cmd == 'export':
        export(con)
    elif a.cmd == 'counts':
        n = 0
        for r in con.execute('SELECT status, COUNT(*) n FROM year_status WHERE year = ? GROUP BY status ORDER BY n DESC, status', (a.year,)):
            print(f"{r['n']:4}  {r['status']}"); n += r['n']
        print(f'{n:4}  total')
    con.commit()


if __name__ == '__main__':
    main()
