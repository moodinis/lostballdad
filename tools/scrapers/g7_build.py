"""g7_raw.csv -> g7_draft.csv (organizer Other, ' (Game 7)' suffix, per CLAUDE.md)."""
import csv, re
from datetime import datetime
FIX_NAMES = {'12u WOOD BAT Turf Challenge': '12U Wood Bat Turf Challenge',
             'TN Game 7 No Play Mothers Day (SATURDAY ONLY)': 'TN Game 7 No Play Mothers Day (Saturday Only)',
             '10u Turf Challenge': '10U Turf Challenge'}
out, skipped = [], []
for r in csv.DictReader(open('g7_raw.csv', encoding='utf-8')):
    m = re.match(r'(\w{3}) (\d+)(?:\s*-\s*(?:(\w{3}) )?(\d+))?, (\d{4})', r['dates'])
    mon1, d1, mon2, d2, y = m.groups()
    start = datetime.strptime(f'{mon1} {d1} {y}', '%b %d %Y').date()
    end = datetime.strptime(f'{mon2 or mon1} {d2 or d1} {y}', '%b %d %Y').date()
    ages = [int(a) for a in re.findall(r'(\d+)U', r['ages'])]
    if start.month != 5:
        skipped.append(f"starts {start}: {r['name']}"); continue
    if max(ages) < 12:
        skipped.append(f"<12U: {r['name']} ({r['ages']})"); continue
    city, st = re.match(r'(.*),\s*([A-Z]{2})$', r['loc']).groups()
    city = re.split(r'\s*[/,]\s*', city)[0].replace('’', "'").replace('Mt. Juliet', 'Mount Juliet')
    name = FIX_NAMES.get(r['name'], r['name']) + ' (Game 7)'
    out.append(dict(name=name, organizer='Other', city=city, state=st, start_date=start, end_date=end,
                    start_age=min(ages), end_age=max(ages), link=r['link'], geo=''))
w = csv.DictWriter(open('g7_draft.csv', 'w', newline='', encoding='utf-8'), fieldnames=list(out[0]))
w.writeheader(); w.writerows(out)
print(len(out), 'rows'); print('\n'.join(skipped))
for o in out: print(o['start_date'], o['start_age'], o['end_age'], o['city'], o['state'], '|', o['name'])
