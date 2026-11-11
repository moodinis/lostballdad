"""NCS (playncs.com) baseball events starting Jan-Jul 2027 -> ncs_raw.csv. Uses plain curl like pbr_all.py."""
import csv, html, re, subprocess, time
B = 'https://playncs.com'
t = lambda s: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()
rows, page = [], 1
while True:
    h = subprocess.run(['curl', '-s', '-L', '--max-time', '40',
                        f'{B}/baseball/Events?page={page}&from=01%2F01%2F2027&to=07%2F31%2F2027'],
                       capture_output=True, text=True).stdout
    cards = h.split('<div class="media ')[1:]
    if not cards:
        break
    for c in cards:
        stature = re.search(r'class="h5 stature">(.*?)</div>', c)
        link = re.search(r'href="(/baseball/Events/Details/[^"]+)"', c)
        body = c.split('class="media-body"', 1)[-1]
        h6 = re.findall(r'<div class="h6">(.*?)</div>', body, re.S)
        h4 = re.findall(r'<div class="h4">(.*?)</div>', body, re.S)
        loc = re.search(r'<span>(.*?)</span>', h6[0]) if h6 else None
        d = re.search(r'class="director">(.*?)</span>', h6[0]) if h6 else None
        if not link or len(h4) < 2:
            continue
        rows.append(dict(stature=t(stature[1]) if stature else '', name=t(h4[0]), dates=t(h4[-1]),
                         loc=t(loc[1]) if loc else '', director=t(d[1]).lstrip('| ') if d else '',
                         ages=t(h6[-1]) if len(h6) > 1 else '', link=B + link[1]))
    if f'page={page + 1}&' not in h:
        break
    page += 1
    time.sleep(1)
w = csv.DictWriter(open('ncs_raw.csv', 'w', newline='', encoding='utf-8'), fieldnames=list(rows[0]))
w.writeheader(); w.writerows(rows)
print(len(rows), 'rows,', page, 'pages')
