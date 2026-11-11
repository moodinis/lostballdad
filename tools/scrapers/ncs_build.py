"""ncs_raw.csv -> ncs_draft.csv (organizer Other, ' (NCS)' suffix)."""
import collections, csv, re, sys
from datetime import datetime, date
sys.argv = ['x']; exec(open('build_draft.py').read().split('rows = list(')[0])   # reuse CITY / fix_caps
out, skipped = [], []
for r in csv.DictReader(open('ncs_raw.csv', encoding='utf-8')):
    m = re.match(r'(\w{3}) (\d+)(?:, (\d{4}))?\s*(?:-\s*(?:(\w{3}) )?(\d+))?, (\d{4})', r['dates'])
    mon1, d1, y1, mon2, d2, y2 = m.groups()
    start = datetime.strptime(f'{mon1} {d1} {y1 or y2}', '%b %d %Y').date()
    end = datetime.strptime(f'{mon2 or mon1} {d2 or d1} {y2}', '%b %d %Y').date()
    ages = [int(a) for a in re.findall(r'(\d+)U', r['ages'])]
    why = ('not 2027 Jan-Jul' if not date(2027, 1, 1) <= start <= date(2027, 7, 31) else
           'league/multi-week' if (end - start).days > 6 or 'league' in r['name'].lower() else
           'showcase' if 'Showcase' in r['stature'] or 'showcase' in r['name'].lower() else
           'no ages' if not ages else '<12U' if max(ages) < 12 else
           'outside US' if not re.search(r', [A-Z]{2}$', r['loc']) or r['loc'][-2:] in ('MX', 'PR') else '')
    if why:
        skipped.append(f"{why}: {r['name']} | {r['loc']} | {r['dates']}"); continue
    city, st = re.match(r'(.*),\s*([A-Z]{2})$', r['loc']).groups()
    city = re.sub(r'\s+Area$', '', city, flags=re.I)
    city = city.title() if city.isupper() else city
    out.append(dict(name=fix_caps(r['name']).strip(' -') + ' (NCS)', organizer='Other', city=city, state=st,
                    start_date=start, end_date=end, start_age=min(ages), end_age=max(ages), link=r['link'], geo=''))
dupes = collections.Counter((o['name'], o['start_date']) for o in out)
for o in out:
    if dupes[(o['name'], o['start_date'])] > 1:
        o['name'] = o['name'][:-6] + f" ({o['city']}) (NCS)"
w = csv.DictWriter(open('ncs_draft.csv', 'w', newline='', encoding='utf-8'), fieldnames=list(out[0]))
w.writeheader(); w.writerows(out)
print(len(out), 'rows'); print('\n'.join(skipped))
for o in out: print(o['start_date'], o['start_age'], o['end_age'], o['city'], o['state'], '|', o['name'])
