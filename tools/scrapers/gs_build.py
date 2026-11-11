"""gs_raw.csv -> gs_draft.csv (organizer Other, ' (Grand Slam)' suffix)."""
import collections, csv, re, sys
from datetime import datetime
exec(open('build_draft.py').read().split('rows = list(')[0])   # reuse fix_caps
LOC = [(r'^Louisville Area$', 'Louisville area', 'Jeffersonville, IN'), (r'Gwinnett', 'Gwinnett County area', 'Lawrenceville, GA'),
       (r'^Forsyth', 'Forsyth/Hall County area', 'Cumming, GA'), (r'^Gainesville/Hall', 'Gainesville', ''),
       (r'Biloxi|Gulfport', 'Gulfport', ''), (r'^West Memphis', 'West Memphis', ''), (r'^Ellijay', 'Ellijay', ''),
       (r'^Metro Area$', 'Jackson area', 'Jackson, MS'), (r'^SALTILLO$', 'Saltillo', '')]
out, skipped = [], []
for r in csv.DictReader(open('gs_raw.csv', encoding='utf-8')):
    m = re.match(r'(\w{3}) (\d+)(?:\s*-\s*(?:(\w{3}) )?(\d+))?, (\d{4})', r['dates'])
    mon1, d1, mon2, d2, y = m.groups()
    start = datetime.strptime(f'{mon1} {d1} {y}', '%b %d %Y').date()
    end = datetime.strptime(f'{mon2 or mon1} {d2 or d1} {y}', '%b %d %Y').date()
    ages = [int(a) for a in r['ages'].split()]
    if not ages or max(ages) < 12:
        skipped.append(f"<12U/no ages: {r['name']} ({r['ages']})"); continue
    if re.search(r'softball|fastpitch', r['name'], re.I):
        skipped.append(f"softball: {r['name']}"); continue
    label, st = re.match(r'(.*),\s*([A-Z]{2})$', r['loc']).groups()
    city, geo = label, ''
    for pat, c, g in LOC:
        if re.search(pat, label):
            city, geo = c, g; break
    out.append(dict(name=fix_caps(r['name']) + ' (Grand Slam)', organizer='Other', city=city, state=st, start_date=start,
                    end_date=end, start_age=min(ages), end_age=max(ages), link=r['link'], geo=geo))
dupes = collections.Counter((o['name'], o['start_date']) for o in out)
for o in out:
    if dupes[(o['name'], o['start_date'])] > 1:
        o['name'] = o['name'][:-len(' (Grand Slam)')] + f" ({o['city']}) (Grand Slam)"
w = csv.DictWriter(open('gs_draft.csv', 'w', newline='', encoding='utf-8'), fieldnames=list(out[0]))
w.writeheader(); w.writerows(out)
print(len(out), 'rows;', len(skipped), 'skipped'); print(collections.Counter(o['state'] for o in out))
for o in out: print(o['start_date'], o['start_age'], o['end_age'], o['city'], o['state'], '|', o['name'])
