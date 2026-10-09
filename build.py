#!/usr/bin/env python3
"""Download the Transport Department timetables and build public/index.html (plus the service worker).

    python3 build.py              download fresh data, then build
    python3 build.py --no-fetch   rebuild from the files already in td/
"""
import datetime, hashlib, json, pathlib, re, subprocess, sys, urllib.request

ROOT = pathlib.Path(__file__).parent
TD = ROOT / 'td'
BASE = 'https://www.td.gov.hk/datagovhk_td/ferry-tt-ft/resources/en/ferry_%s_%s_eng.csv'
ROUTES = ['central_pc', 'central_ysw', 'central_skw', 'central_mw', 'central_cc', 'central_db', 'mawan_c', 'mawan_tw',
          'np_hh', 'np_klnc', 'np_ktak', 'swh_kt', 'swh_skt', 'db_mw', 'tm_tc_slw_to', 'abd_skw', 'abd_ysw', 'c_hh',
          'pc_mw_cmw_cc', 'db_pc_tm']


def fetch():
    TD.mkdir(exist_ok=True)
    for r in ROUTES:
        for kind, name in (('timetable', r), ('faretable', r + '_fare')):
            req = urllib.request.Request(BASE % (r, kind), headers={'User-Agent': 'hk-ferry-build'})
            body = urllib.request.urlopen(req, timeout=60).read()
            if b',' not in body[:200] or body.lstrip()[:1] == b'<':
                sys.exit(f'{r} {kind}: not a CSV, refusing to publish')
            (TD / f'{name}.csv').write_bytes(body)
    print('downloaded', len(ROUTES) * 2, 'files')


def main():
    if '--no-fetch' not in sys.argv:
        fetch()
    data = ROOT / 'build' / 'data.json'
    data.parent.mkdir(exist_ok=True)
    subprocess.run([sys.executable, str(ROOT / 'src' / 'make_data.py'), str(TD), str(data)], check=True)
    d = json.loads(data.read_text())
    # Sanity check: a broken download must not replace a good site.
    empty = [r['id'] for r in d['routes'] if not r['freq'] and not any(r['dirs'].values())]
    if len(d['routes']) < 30 or empty:
        sys.exit(f'sanity check failed: {len(d["routes"])} routes, empty: {empty}')

    built = datetime.date.today().strftime('%-d %b %Y')
    page = (ROOT / 'src' / 'template.html').read_text()
    page = re.sub(r'<link rel="stylesheet" href="https://fonts[^>]*>\n?', '', page)  # offline: system fonts only
    page = page.replace('__DATA__', json.dumps(d, ensure_ascii=False, separators=(',', ':'))).replace('__BUILT__', built)
    page = page.replace('</script>\n', "</script>\n<script>if('serviceWorker' in navigator)navigator.serviceWorker.register('sw.js').catch(function(){})</script>\n", 1) if False else page
    html = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<meta name="theme-color" content="#0a6f7d"><link rel="manifest" href="manifest.webmanifest">'
            '<link rel="apple-touch-icon" href="apple-touch-icon.png">'
            '<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes">'
            '<meta name="apple-mobile-web-app-title" content="Ferries">'
            '<style>:root{color-scheme:light dark;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
            'body{margin:0}[hidden]{display:none!important}</style></head><body>'
            + page +
            "<script>if('serviceWorker' in navigator)navigator.serviceWorker.register('sw.js').catch(function(){})</script>"
            '</body></html>')
    out = ROOT / 'public'
    (out / 'index.html').write_text(html)
    version = 'ferry-' + hashlib.sha256(html.encode()).hexdigest()[:12]
    (out / 'sw.js').write_text((ROOT / 'src' / 'sw.js').read_text().replace('__VERSION__', version))
    print(f'built {len(d["routes"])} routes, {len(html) // 1024} KB, cache {version}')


main()
