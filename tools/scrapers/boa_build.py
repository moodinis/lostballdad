"""Ballparks of America 2027 summer event pages -> boa_geo.csv (organizer Other, ' (Ballparks of America)' suffix)."""
import csv, html, re
from datetime import datetime
IDS = '46705 46753 46754 46755 46756 46706 46757 46758 46759 46760'.split()
out = []
for i in IDS:
    h = open(f'boa_ev_{i}.html').read()
    t = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<script.*?</script>|<style.*?</style>|<[^>]+>', '|', h, flags=re.S)))
    t = re.sub(r'(\s*\|\s*)+', '|', t)
    name = re.search(r'EVENT DETAILS\|(.*?)\|Dates', t)[1]
    m = re.search(r'Dates\|(\w{3}) (\d+) – (\w{3}) (\d+), (\d{4})', t)
    s = datetime.strptime(f'{m[1]} {m[2]} {m[5]}', '%b %d %Y').date()
    e = datetime.strptime(f'{m[3]} {m[4]} {m[5]}', '%b %d %Y').date()
    groups = re.search(r'Age Groups\|(.*?)\|', t)[1]
    ages = [int(a) for a in re.findall(r'(\d+)(?:U|-)', groups)] + [int(a) for a in re.findall(r'-(\d+)U', groups)]
    out.append(dict(name=re.sub(r'^2027 ', '', name) + ' (Ballparks of America)', organizer='Other', city='Branson', state='MO',
                    start_date=s, end_date=e, start_age=min(ages), end_age=max(ages),
                    link=f'https://www.ballparksofamerica.com/event-{i}', lat='36.6006', lng='-93.2427'))
    print(s, e, groups, '|', out[-1]['name'], min(ages), max(ages))
w = csv.DictWriter(open('boa_geo.csv', 'w', newline=''), fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
