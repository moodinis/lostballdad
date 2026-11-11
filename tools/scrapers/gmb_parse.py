"""playgmb.com/tournaments/ -> gmb_raw.csv (one row per event card)."""
import csv, html, re
from datetime import date
MON = {m: i for i, m in enumerate('January February March April May June July August September October November December'.split(), 1)}
h = html.unescape(open('gmb.html', encoding='utf-8').read())
rows = []
for e in h.split('<div class="entry">')[1:]:
    d = re.search(r'<span class="date">\s*(.*?)<br', e, re.S)[1].strip()
    name = re.search(r'<span class="name">(.*?)</span>', e, re.S)[1].strip()
    loc = re.search(r'</span>\s*([^<]+?)<br />', e)[1].strip()
    ages = re.findall(r'<div class="age">(.*?)</div>', e)
    link = re.search(r'href="(https://go\.play\w+\.com/(?:public/)?events/[^"/]+)"', e)[1]
    # "March 6th - 7th 2027", "May 30th - June 1st 2027", "March 27th 2027"
    m = re.match(r'(\w+) (\d+)\w* (?:- (?:(\w+) )?(\d+)\w* )?(\d{4})', d)
    m1, d1, m2, d2, y = MON[m[1]], int(m[2]), MON.get(m[3], MON[m[1]]), int(m[4] or m[2]), int(m[5])
    s = re.search(r'-(\d\d)-(\d\d)-(\d{4})$', link)
    slug = date(int(s[3]), int(s[1]), int(s[2])) if s else None
    start = date(y, m1, d1)
    end = date(y + (m2 < m1), m2, d2)
    rows.append(dict(name=name, loc=loc, start=start, end=end, slug_start=slug, card=d, ages=' '.join(ages), link=link))
w = csv.DictWriter(open('gmb_raw.csv', 'w', newline='', encoding='utf-8'), fieldnames=list(rows[0]))
w.writeheader(); w.writerows(rows)
print(len(rows), 'cards')
for r in rows:
    if r['slug_start'] != r['start']: print('DATE MISMATCH', r['card'], 'slug', r['slug_start'], '|', r['name'])
