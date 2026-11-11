"""Grand Slam Sports Tournaments (grandslamtournaments.com) events starting Jan-Jul 2027 -> gs_raw.csv (plain curl)."""
import csv, html, re, subprocess, time
B = 'https://www.grandslamtournaments.com'
t = lambda s: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()
rows, seen, page = [], set(), 1
while True:
    h = subprocess.run(['curl', '-s', '-L', '--max-time', '40',
                        f'{B}/baseball/Events?page={page}&from=01%2F01%2F2027&to=07%2F31%2F2027'],
                       capture_output=True, text=True).stdout
    cards = re.split(r'<div class="media[^"]*" data-eventId="', h)[1:]
    if not cards:
        break
    for c in cards:
        eid = c.split('"', 1)[0]
        if eid in seen:
            continue
        seen.add(eid)
        name = re.search(r'<div class="h3[^"]*">\s*<strong>(.*?)</strong>', c, re.S)
        dates = re.search(r'<div class="h4[^"]*">(.*?)</div>', c, re.S)
        loc = re.search(r'<div class="h5">\s*<strong>(.*?)</strong>', c, re.S)
        ages = re.findall(r'data-agenumber="(\d+)"', c)
        rows.append(dict(id=eid, name=t(name[1]) if name else '', dates=t(dates[1]) if dates else '',
                         loc=t(loc[1]) if loc else '', ages=' '.join(ages), link=f'{B}/baseball/Events/Details/{eid}'))
    if f'page={page + 1}&' not in h.replace('&amp;', '&'):
        break
    page += 1
    time.sleep(1)
w = csv.DictWriter(open('gs_raw.csv', 'w', newline='', encoding='utf-8'), fieldnames=list(rows[0]))
w.writeheader(); w.writerows(rows)
print(len(rows), 'rows,', page, 'pages')
