"""Fill lat/lng for a draft tournament CSV via OpenStreetMap Nominatim, writing <input>_geo.csv.

Usage: python tools/geocode.py draft.csv

Input columns: name,organizer,city,state,start_date,end_date,start_age,end_age,link,geo
  geo (optional, may be blank) overrides the lookup:
    - "City, ST"      -> geocode that instead of the row's city/state (e.g. "Louisville, KY" for "Kentuckiana")
    - "lat;lng"       -> use these coordinates as-is (for places Nominatim gets wrong)
Only city + state are sent to Nominatim. Requests are throttled to ~1/sec per its usage policy.
Review the output: same-named towns occasionally resolve to the wrong place (e.g. Marion, IL).
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request

src = sys.argv[1]
out = src.replace('.csv', '_geo.csv')
cache = {}


def lookup(q):
    if q in cache:
        return cache[q]
    url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode(
        {'q': q + ', USA', 'format': 'json', 'limit': 1, 'countrycodes': 'us'})
    req = urllib.request.Request(url, headers={'User-Agent': 'tourney-map-geocoder/1.0'})
    for _ in range(4):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                res = json.load(r)
            break
        except Exception as e:
            print('retry', q, e)
            time.sleep(5)
    else:
        res = []
    time.sleep(1.1)
    cache[q] = (round(float(res[0]['lat']), 4), round(float(res[0]['lon']), 4)) if res else None
    print(f'{q:35} -> {cache[q]}')
    return cache[q]


with open(src, newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
missing = []
for r in rows:
    q = r.pop('geo', '') or f"{r['city']}, {r['state']}"
    ll = tuple(map(float, q.split(';'))) if ';' in q else lookup(q)
    if not ll:
        missing.append(q)
    r['lat'], r['lng'] = ll if ll else ('', '')
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print('rows', len(rows), 'missing', missing)
