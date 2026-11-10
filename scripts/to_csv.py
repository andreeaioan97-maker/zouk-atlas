import json,csv,sys
d=json.load(open(sys.argv[1]))
w=csv.writer(open(sys.argv[2],'w',newline=''))
w.writerow(['name','city','country','style','2025','2026','2027','status_2027','website','instagram','facebook_page','facebook_event_latest','sources'])
for f in d:
  e=f['editions']; g=lambda y: '' if y not in e else ('?' if not e[y].get('start') else (e[y]['start'] if not e[y].get('end') else f"{e[y]['start']} → {e[y]['end']}"))
  w.writerow([f['name'],f['city'],f['country'],f['style'],g('2025'),g('2026'),g('2027'),f['status_2027'],f['website'] or '',f['instagram'] or '',f['facebook_page'] or '',f['facebook_event_latest'] or '',' '.join(e[y]['source'] for y in sorted(e))])
