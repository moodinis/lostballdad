"""gmb_raw.csv -> gmb_draft.csv (organizer Other, '(GMB)' / '(AAYBA)' suffix)."""
import collections, csv, re
out, skipped = [], []
for r in csv.DictReader(open('gmb_raw.csv', encoding='utf-8')):
    if re.search(r'Sanctioning|Credits', r['name']):
        skipped.append(f"admin: {r['name']}"); continue
    ages = [int(a) for a in re.findall(r'(\d+)U', r['ages'])]
    if max(ages) < 12:
        skipped.append(f"<12U: {r['name']} ({r['ages']})"); continue
    org = 'AAYBA' if 'AAYBA' in r['name'] else 'GMB'
    name = re.sub(r'^2027 (GMB |AAYBA )?', '', r['name']).replace(' powered by GMB Elite', '')
    city, st = re.match(r'(.*),\s*([A-Z]{2})$', r['loc']).groups()
    city = city.replace('Saint Charles', 'St. Charles')
    out.append(dict(name=f'{name} ({org})', organizer='Other', city=city, state=st, start_date=r['start'],
                    end_date=r['end'], start_age=min(ages), end_age=max(ages), link=r['link'], geo=''))
dupes = collections.Counter((o['name'], o['start_date']) for o in out)
for o in out:
    if dupes[(o['name'], o['start_date'])] > 1:
        o['name'] = o['name'].replace(' (', f" – {o['city']} (", 1)
        print('disambiguated', o['name'])
w = csv.DictWriter(open('gmb_draft.csv', 'w', newline='', encoding='utf-8'), fieldnames=list(out[0]))
w.writeheader(); w.writerows(out)
print(len(out), 'rows'); print('\n'.join(skipped))
