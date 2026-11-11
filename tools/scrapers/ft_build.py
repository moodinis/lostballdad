"""ft_raw.json -> ft_draft_geo.csv (organizer Five Tool) + ft_match.txt (existing DB rows matched by state + start date)."""
import csv, json, re, sys
sys.path.insert(0, '/home/cctom/projects/tourneysv2')
import os; os.chdir('/home/cctom/projects/tourneysv2'); import db; os.chdir(os.path.dirname(os.path.abspath(__file__)))
conn = db.get_conn(); cur = conn.cursor()
cur.execute("select id,name,state,start_date from tournaments where organizer_id=(select id from organizers where name='Five Tool') and start_date>='2027-01-01'")
existing = [(i, n, s, str(d)) for i, n, s, d in cur.fetchall()]
words = lambda s: set(re.findall(r'[a-z]+', s.lower())) - {'five', 'tool', 'the', 'texas', 'california', 'youth', 'south', 'norcal', 'socal'}
B = 'https://events.fivetool.org/events/'
out, skipped, matches = [], [], []
for e in sorted(json.load(open('ft_raw.json')), key=lambda e: e['start_date']):
    s = e['start_date'][:10]
    if not '2027-01-01' <= s <= '2027-07-31':
        continue
    rng = e['division_range_str'] or ''
    ages = [int(a) for a in re.findall(r'(\d+)U', rng)] + ([18] if 'High School' in rng else [])
    if re.search(r'Camp\b|Combine|Select Series|Japan', e['name']) or not re.search(r'\d+U', rng):
        skipped.append(f"{e['name']} ({rng})"); continue
    if max(ages) < 12:
        skipped.append(f"<12U {e['name']}"); continue
    st = e['state'].strip()
    m = [x for x in existing if x[2] == st and x[3] == s and len(words(x[1]) & words(e['name'])) >= 1]
    if m:
        matches.append((m[0][0], m[0][1], e['name'], B + e['url_key'])); continue
    city = re.sub(r'Dallas-F(?:or)?t\.? Worth', 'Dallas-Fort Worth', e['city'].strip())
    lat, lng = float(e['latitude']), float(e['longitude'])
    if city == 'Riverside':
        lat, lng = 33.9806, -117.3755          # platform pin is the county centroid in the desert
    out.append(dict(name=re.sub(r'\s+', ' ', e['name']).strip(), organizer='Five Tool', city=city, state=st, start_date=s,
                    end_date=e['end_date'][:10], start_age=min(ages), end_age=max(ages), link=B + e['url_key'],
                    lat=f'{lat:.4f}', lng=f'{lng:.4f}'))
w = csv.DictWriter(open('ft_draft_geo.csv', 'w', newline=''), fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print(len(out), 'new rows'); print('skipped', skipped)
for m in matches: print('MATCH', m)
json.dump(matches, open('ft_match.json', 'w'))
