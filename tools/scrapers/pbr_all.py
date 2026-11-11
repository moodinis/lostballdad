"""All PBR tournament labels -> pbr_raw.json, via the listing page's own ajax-events call (cookie + CSRF, like a browser)."""
import json, re, subprocess, time, urllib.parse
B = 'https://tournaments.prepbaseballreport.com'
LABELS = 'droplight-grand-park glover-park jennings kansas-city lakepoint new-york ocee-park river-run-park stl summer-championships the-rock usa-stadium world-series'.split()
JAR = 'pbr_all.jar'
open(JAR, 'w').close()


def get(u, d=None):
    cmd = ['curl', '-s', '--max-time', '30', '-b', JAR, '-c', JAR, u] + (['--data', d] if d else [])
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
events = {}
for lab in LABELS:
    page_html = get(f'{B}/label/{lab}')
    lid = re.search(r"var event_label_id = '(\d+)'", page_html)[1]
    tok = json.loads(get(f'{B}/refresh-csrf'))['csrf_token']
    n, p = 0, 1
    while True:
        d = json.loads(get(f'{B}/ajax-events', urllib.parse.urlencode(dict(
            page=p, layout='full', past_events='false', events_exits='', organization_id='', event_label_id=lid, _token=tok))))
        ev = d.get('eventlist') or []
        if not ev:
            break
        for e in ev:
            e['_labels'] = events.get(e['url_key'], {}).get('_labels', []) + [lab]
            events[e['url_key']] = e
        n += len(ev); p += 1
        time.sleep(0.7)
    print(f'{lab} (id {lid}): {n} events')
json.dump(list(events.values()), open('pbr_raw.json', 'w'))
print('unique events', len(events))
