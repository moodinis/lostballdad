"""Parse Triple Crown GetFilteredEventSchedule state pages (upcoming section) -> tc_raw.csv"""
import csv, glob, html, re, sys
rows = []
for f in sorted(glob.glob(sys.argv[1] + '/tcapi_*.html')):
    up = open(f).read().split('Past Events')[0].split('Upcoming Events')[-1]
    t = html.unescape(re.sub(r'<[^>]+>', '|', up))
    t = re.sub(r'\s*\|[\s|]*', '|', t)
    links = [l for l in re.findall(r'href="([^"]+)"', up) if 'maps.google' not in l]
    evs = re.findall(r'\|(\d+)\|(\w{3})\|(\d{4})\|(.*?)\|\w{3}, (\w{3} \d+) - \w{3}, (\w{3} \d+)\|([^|]*)(?=\|)', t)
    for e, l in zip(evs, links):
        rows.append(dict(name=e[3], year=e[2], start=e[4], end=e[5], loc=e[6], link=l))
w = csv.DictWriter(open('tc_raw.csv', 'w', newline=''), fieldnames=list(rows[0]))
w.writeheader(); w.writerows(rows)
for r in rows: print(r)
