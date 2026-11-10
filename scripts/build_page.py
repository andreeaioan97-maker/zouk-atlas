import json, sys
src, tpl, out = sys.argv[1:4]
d = json.load(open(src))
rows, asof = [], max(f.get('last_checked') or '' for f in d)
for f in d:
    e = f['editions']
    prev = [e[y] for y in sorted(e) if y < '2027' and e[y].get('start')]
    rows.append({k: f.get(k) for k in ('name', 'city', 'country', 'style', 'website', 'instagram')} | {
        'status': f['status_2027'], 'note': f.get('note_2027'),
        'e27': e.get('2027'), 'last': prev[-1] if prev else None})
html = open(tpl).read().replace('/*DATA*/[]', json.dumps(rows, ensure_ascii=False).replace('</', '<\\/')).replace('/*ASOF*/', asof)
open(out, 'w').write(html)
print(len(rows), asof, len(html))
