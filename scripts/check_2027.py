#!/usr/bin/env python3
"""Monthly 2027 check for the Zouk Atlas festival list.

Drives Orca's built-in browser (already logged in to Instagram and Facebook)
and writes a report for the agent to review. It never edits the data itself.

  python3 -I scripts/check_2027.py --out reports/raw/2027-check-YYYY-MM

Exit codes: 0 ok, 2 login missing (report says which), 1 other error.
Reads only page text: Instagram profile header + latest post captions, and
the main column of the DJ Mesmes Facebook page (never chats/notifications).
"""
import argparse, json, os, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'festivals.json'
ORCA = os.environ.get('ORCA_CLI_COMMAND') or '/Applications/Orca.app/Contents/Resources/bin/orca'
WORKTREE = 'path:' + str(ROOT)
MESMES = 'https://www.facebook.com/zoukineurope'
DONE = ('listed', 'likely cancelled')


def orca(*args, timeout=90):
    r = subprocess.run([ORCA, *args, '--json'], capture_output=True, text=True, timeout=timeout)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {'ok': False, 'raw': (r.stdout + r.stderr)[:300]}


def ev(page, js):
    d = orca('eval', '--page', page, '--expression', js)
    return (d.get('result') or {}).get('result')


def find_tab(domain, start_url):
    tabs = (orca('tab', 'list', '--worktree', WORKTREE).get('result') or {}).get('tabs', [])
    for t in tabs:
        if domain in (t.get('url') or ''):
            return t['browserPageId']
    d = orca('tab', 'create', '--worktree', WORKTREE, '--url', start_url)
    time.sleep(6)
    return d['result']['browserPageId']


def logged_in(page, names):
    c = (orca('cookie', 'get', '--page', page).get('result') or {}).get('cookies', [])
    have = {x.get('name') for x in c}
    return all(n in have for n in names)


IG_JS = r'''(()=>{const m=document.querySelector("main")||document.body;const h=m.querySelector("header");
const b=h&&[...h.querySelectorAll("span,div[role=button]")].find(e=>e.innerText.trim()=="more");if(b)b.click();
return new Promise(r=>setTimeout(()=>r(JSON.stringify({bio:h?h.innerText:m.innerText.slice(0,600),
posts:[...m.querySelectorAll("a[href*='/p/'],a[href*='/reel/']")].slice(0,12).map(a=>[a.getAttribute("href"),[...a.querySelectorAll("img")].map(i=>i.alt).join(" ")])})),1500))})()'''

MES_JS = r'''(async()=>{for(const b of document.querySelectorAll("[data-ad-preview=message] [role=button],[data-ad-comet-preview=message] [role=button]")){if(/See more/.test(b.innerText))b.click()}
await new Promise(r=>setTimeout(r,1500));
const out=[...document.querySelectorAll("[data-ad-preview=message],[data-ad-comet-preview=message]")].map(m=>m.innerText.replace(/\s+/g," ").slice(0,600));
window.scrollBy(0,2500);return JSON.stringify(out)})()'''

KEY = re.compile(r'2027|2028|save the date|next edition|new date', re.I)


def check_instagram(page, fests, out):
    rows = []
    for f in fests:
        orca('goto', '--page', page, '--url', f['instagram'].rstrip('/') + '/')
        time.sleep(8)
        try:
            d = json.loads(ev(page, IG_JS))
        except Exception:
            d = {'bio': '', 'posts': [], 'err': 'could not read profile'}
        bio = d.get('bio', '')
        if "isn't available" in bio or 'Sorry, this page' in bio:
            d['err'] = 'profile not available (renamed or removed?)'
        hits = [[h, c[:600]] for h, c in d.get('posts', []) if KEY.search(c)]
        rows.append({'id': f['id'], 'name': f['name'], 'url': f['instagram'], 'bio': bio[:600],
                     'bio_hit': bool(KEY.search(bio)), 'hits': hits, 'err': d.get('err')})
        time.sleep(6)  # stay slow so Meta does not flag the account
    (out / 'instagram.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    return rows


def check_mesmes(page, fests_all, out, scrolls=25):
    orca('goto', '--page', page, '--url', MESMES)
    time.sleep(8)
    seen = {}
    for _ in range(scrolls):
        try:
            for t in json.loads(ev(page, MES_JS)):
                k = t[:60]
                if len(t) > len(seen.get(k, '')):
                    seen[k] = t
        except Exception:
            pass
        time.sleep(3.5)
    known = [f['name'].lower() for f in fests_all]
    rows = []
    for t in seen.values():
        m = re.search(r'New (?:Zouk )?event from (\S+)\s+in (.*?)!\s*(.*?) (20\d\d[-/]\d\d[-/]\d\d)', t)
        if not m or not m.group(4).startswith('2027'):
            continue
        name = m.group(3).strip()
        words = [w for w in re.findall(r'\w{4,}', name.lower()) if w not in ('zouk', 'festival', 'brazilian', 'marathon', 'lambada', 'congress', 'weekend')]
        rows.append({'text': t, 'name': name, 'maybe_known': any(all(w in k for w in words[:2]) for k in known) if words else True})
    (out / 'mesmes.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--limit', type=int, default=0, help='check only the first N festivals (testing)')
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    fests_all = json.load(open(DATA))
    todo = [f for f in fests_all if f['status_2027'] not in DONE and f.get('instagram')]
    if a.limit:
        todo = todo[:a.limit]

    ig = find_tab('instagram.com', 'https://www.instagram.com/')
    fb = find_tab('facebook.com', 'https://www.facebook.com/')
    missing = [n for n, ok in (('Instagram', logged_in(ig, ['sessionid'])), ('Facebook', logged_in(fb, ['c_user']))) if not ok]
    rep = [f'# 2027 check — {time.strftime("%Y-%m-%d")}', '']
    if missing:
        rep.append(f'**Login missing: {", ".join(missing)}.** Log in again in the Orca browser tab for this workspace, then re-run.')
        (out / 'report.md').write_text('\n'.join(rep) + '\n')
        print('\n'.join(rep)); sys.exit(2)

    igr = check_instagram(ig, todo, out)
    mes = check_mesmes(fb, fests_all, out) if not a.limit else []

    rep += [f'Checked {len(igr)} Instagram profiles of festivals without 2027 dates.', '', '## Instagram leads', '']
    for r in igr:
        if r['bio_hit'] or r['hits']:
            rep.append(f"### {r['name']} (`{r['id']}`)\n- Bio: {r['bio'].replace(chr(10), ' | ')[:400]}")
            for h, c in r['hits'][:3]:
                rep.append(f"- https://www.instagram.com{h} — {c.replace(chr(10), ' ')[:400]}")
            rep.append('')
    errs = [r for r in igr if r.get('err')]
    if errs:
        rep += ['## Profiles that could not be read', ''] + [f"- `{r['id']}`: {r['err']} ({r['url']})" for r in errs] + ['']
    rep += ['## DJ Mesmes page: 2027 events', '']
    for m in mes:
        rep.append(f"- {'(probably known) ' if m['maybe_known'] else '**NEW?** '}{m['text'][:300]}")
    (out / 'report.md').write_text('\n'.join(rep) + '\n')
    print(out / 'report.md')


if __name__ == '__main__':
    main()
