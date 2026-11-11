"""pbr_raw.json -> pbr_draft.csv (organizer Other, '(PBR)' suffix; venue lat/lng from PBR as geo)."""
import collections, csv, json, re
B = 'https://tournaments.prepbaseballreport.com/events/'
out, skipped = [], []
for e in sorted(json.load(open('pbr_raw.json')), key=lambda e: e['start_date']):
    ages = [int(a) for a in re.findall(r'(\d+)U', e.get('division_range_str') or '', re.I)]
    if not ages:
        skipped.append(f"no ages: {e['name']}"); continue
    if max(ages) < 12:
        skipped.append(f"<12U: {e['name']} ({e['division_range_str']})"); continue
    name = re.sub(r'\b(\d+)u\b', r'\1U', re.sub(r'\s+', ' ', e['name']).strip())
    city = e['city'].strip().replace('Kansas Ciy', 'Kansas City')
    lat, lng = e.get('latitude'), e.get('longitude')
    geo = f'{float(lat):.4f};{float(lng):.4f}' if lat and lng and float(lat) else ''
    if city == 'Westfield' and e['state'].strip() == 'IN' and abs(float(lat or 0) - 40.04) > 0.2:
        geo = '40.0428;-86.1275'   # PBR's venue pin for this event is near Marion, IN; Grand Park is in Westfield
    if geo == '39.0997;-94.5786' and e['state'].strip() == 'KS':
        geo = '39.1142;-94.6275'   # generic downtown-KCMO pin; these use the same KCK complexes as PBR's other KC events
    out.append(dict(name=f'{name} (PBR)', organizer='Other', city=city, state=e['state'].strip(),
                    start_date=e['start_date'][:10], end_date=e['end_date'][:10], start_age=min(ages), end_age=max(ages),
                    link=B + e['url_key'], geo=geo))
dupes = collections.Counter((o['name'], o['start_date']) for o in out)
for o in out:
    if dupes[(o['name'], o['start_date'])] > 1:
        o['name'] = o['name'][:-len(' (PBR)')] + f" ({o['city']}) (PBR)"
w = csv.DictWriter(open('pbr_draft.csv', 'w', newline='', encoding='utf-8'), fieldnames=list(out[0]))
w.writeheader(); w.writerows(out)
print(len(out), 'rows;', sum(not o['geo'] for o in out), 'without coords;', sum(dupes[k] > 1 for k in dupes), 'dup groups')
print('\n'.join(skipped))
