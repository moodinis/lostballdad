"""Game 7 events starting in Jun-Jul 2027 -> g7_raw.csv"""
import csv, html, re, time, urllib.request
from datetime import datetime
B = 'https://www.game7baseball.com'
rows, page = [], 1
while True:
    url = f'{B}/baseball/Events?from=06%2F01%2F2027&to=07%2F31%2F2027&page={page}'
    h = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode()
    cards = re.split(r"<div class=\"media(?: new| )\">", h)[1:]
    if not cards:
        break
    for c in cards:
        t = lambda s: html.unescape(re.sub(r'<[^>]+>|\s+', ' ', s)).strip()
        link = re.search(r'href="(/baseball/Events/Details/[^"]+)"', c)
        h6 = re.findall(r'<div class="h6">(.*?)</div>', c, re.S)
        h4 = re.findall(r'<div class="h4">(.*?)</div>', c, re.S)
        if not link or len(h4) < 2:
            continue
        loc, _, venue = t(h6[0]).partition('|')
        rows.append(dict(name=t(h4[0]), loc=loc.strip(), venue=venue.strip(), dates=t(h4[1]),
                         ages=t(h6[1]) if len(h6) > 1 else '', link=B + link[1]))
    if f'page={page + 1}' not in h:
        break
    page += 1
    time.sleep(1)
w = csv.DictWriter(open('g7_raw.csv', 'w', newline='', encoding='utf-8'), fieldnames=list(rows[0]))
w.writeheader(); w.writerows(rows)
print(len(rows), 'rows,', page, 'pages')
