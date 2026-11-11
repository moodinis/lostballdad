"""pw_raw.json -> pw_draft_geo.csv: Prospect Wire team tournaments Jan-Jul 2027 (no HS Varsity), ' (Prospect Wire)' suffix."""
import csv, json, re
CITY = {'Saint Lucie West': 'Port St. Lucie', 'Polk County': 'Auburndale', 'Palm Beach': 'West Palm Beach'}
out, skipped = [], []
for e in sorted(json.load(open('pw_raw.json')), key=lambda e: e['start_date']):
    s = e['start_date'][:10]
    if not '2027-01-01' <= s <= '2027-07-31':
        continue
    rng = e['division_range_str'] or ''
    ages = [int(a) for a in re.findall(r'(\d+)U', rng)]
    if not ages or 'Varsity' in rng:
        skipped.append(f"{e['name']} ({rng})"); continue
    if max(ages) < 12:
        skipped.append(f"<12U {e['name']}"); continue
    name = re.sub(r'\s+Powered [Bb]y Prospect Wire', '', e['name']).strip()
    out.append(dict(name=name + ' (Prospect Wire)', organizer='Other', city=CITY.get(e['city'].strip(), e['city'].strip()),
                    state=e['state'].strip(), start_date=s, end_date=e['end_date'][:10], start_age=min(ages), end_age=max(ages),
                    link='https://play.prospectwire.com/events/' + e['url_key'],
                    lat=f"{float(e['latitude']):.4f}", lng=f"{float(e['longitude']):.4f}"))
w = csv.DictWriter(open('pw_draft_geo.csv', 'w', newline=''), fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print(len(out), 'rows; skipped', skipped)
for o in out: print(o['start_date'], o['start_age'], o['end_age'], o['city'], o['state'], o['lat'], o['lng'], '|', o['name'])
