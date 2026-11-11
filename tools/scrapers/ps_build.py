"""ps_raw.json -> ps_draft_geo.csv: team tournaments only (no Varsity / Pitcher-Only selects / collegiate), ' (Prospect Select)' suffix."""
import csv, json, re
SESSIONS = {'copy-of-black-bear-classic-greenville-sc-06-16-2027': [
    ('Black Bear Classic 18U', '2027-06-16', '2027-06-20', 18, 18), ('Black Bear Classic 13U', '2027-06-24', '2027-06-28', 13, 13)],
    'boston-classic-boston-ma-07-07-2027': [('Boston Classic 16U', '2027-07-07', '2027-07-12', 16, 16),
                                           ('Boston Classic 18U', '2027-07-12', '2027-07-16', 18, 18)]}
out, skipped = [], []
for e in sorted(json.load(open('ps_raw.json')), key=lambda e: e['start_date']):
    if e['start_date'] > '2027-07-31':
        continue
    rng = e['division_range_str'] or ''
    link = f"https://play.ps-baseball.com/events/{e['url_key']}"
    base = dict(organizer='Other', city=e['city'], state=e['state'], link=link, lat=e['latitude'], lng=e['longitude'])
    if e['url_key'] in SESSIONS:
        for n, s, en, a1, a2 in SESSIONS[e['url_key']]:
            out.append(dict(name=n + ' (Prospect Select)', start_date=s, end_date=en, start_age=a1, end_age=a2, **base))
        continue
    ages = [int(a) for a in re.findall(r'(\d+)U', rng)]
    if re.search(r'Varsity|Pitcher Only|Collegiate', rng) or not ages:
        skipped.append(f"{e['name']} ({rng})"); continue
    if 'Junior College' in rng:
        ages.append(18)
    if max(ages) < 12:
        skipped.append(f"<12U {e['name']} ({rng})"); continue
    city = {'Palm Beach': 'West Palm Beach'}.get(e['city'], e['city'])
    out.append(dict(name=e['name'] + ' (Prospect Select)', start_date=e['start_date'], end_date=e['end_date'],
                    start_age=min(ages), end_age=max(ages), **{**base, 'city': city}))
cols = 'name,organizer,city,state,start_date,end_date,start_age,end_age,link,lat,lng'.split(',')
w = csv.DictWriter(open('ps_draft_geo.csv', 'w', newline=''), fieldnames=cols); w.writeheader(); w.writerows(out)
print(len(out), 'rows; skipped:', skipped)
for o in out: print(o['start_date'], o['start_age'], o['end_age'], o['city'], o['state'], o['lat'], o['lng'], '|', o['name'])
