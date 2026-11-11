"""Prospect Select (Playbook365, same platform as PBR) upcoming events -> ps_raw.json via the listing's ajax-events call."""
import json, subprocess, sys, time, urllib.parse
B = sys.argv[1] if len(sys.argv) > 1 else 'https://play.ps-baseball.com'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'ps_raw.json'
JAR = OUT + '.jar'
open(JAR, 'w').close()
get = lambda u, d=None: subprocess.run(['curl', '-s', '--max-time', '30', '-b', JAR, '-c', JAR, u] + (['--data', d] if d else []),
                                       capture_output=True, text=True, check=True).stdout
get(f'{B}/events')
tok = json.loads(get(f'{B}/refresh-csrf'))['csrf_token']
events, p = {}, 1
while True:
    d = json.loads(get(f'{B}/ajax-events', urllib.parse.urlencode(dict(
        page=p, layout='full', past_events='false', events_exits='', organization_id='', event_label_id='', _token=tok))))
    ev = d.get('eventlist') or []
    if not ev:
        break
    for e in ev:
        events[e['url_key']] = e
    p += 1
    time.sleep(0.7)
json.dump(list(events.values()), open(OUT, 'w'))
print('events', len(events), 'pages', p - 1)
