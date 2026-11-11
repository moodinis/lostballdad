"""Scrape USSSA state baseball sites for events starting in the target months -> usssa_raw.csv.
Target months are hard-coded below: edit the (2027, 6)/(2027, 7) checks."""
import csv, html, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

STATES = ('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY '
          'NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY').split()
MON = {m: i for i, m in enumerate('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(), 1)}
OUT = sys.argv[1] if len(sys.argv) > 1 else 'usssa_raw.csv'


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (tourney-map research)'})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(3)
        except Exception:
            time.sleep(3)
    return None


def text(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()


def parse_date(s):
    # "Dec 4-6", "May 1", "Apr 30-May 2", "May 29 - Jun 1"
    m = re.match(r'([A-Z][a-z]{2})\w*\s+(\d+)(?:\s*-\s*(?:([A-Z][a-z]{2})\w*\s+)?(\d+))?', s)
    if not m:
        return None
    m1, d1, m2, d2 = MON[m[1]], int(m[2]), MON[m[3]] if m[3] else MON[m[1]], int(m[4] or m[2])
    return m1, d1, m2, d2


def scrape(st):
    base = f'https://{st.lower()}baseball.usssa.com/events/'
    rows, year, prev, page = [], 2026, 0, 1
    while True:
        h = get(base + (f'?paged={page}' if page > 1 else ''))
        if not h:
            break
        cards = h.split('<div class="events-item-wrapper">')[1:]
        if not cards:
            break
        done = False
        for c in cards:
            c = c.split('<div class="event-block grid-item">')[0]
            link = re.search(r'events-list-elem-title">\s*<a href="([^"]+)"', c)
            title = re.search(r'events-list-elem-title">\s*<a [^>]*>(.*?)</a>', c, re.S)
            info = re.findall(r'<li[^>]*>(.*?)</li>', re.search(r'events-list-elem-info">(.*?)</ul>', c, re.S)[1], re.S)
            lst = re.search(r'events-list-elem-list">(.*?)</ul>', c, re.S)
            lst = [text(x) for x in re.findall(r'<li[^>]*>(.*?)</li>', lst[1], re.S)] if lst else []
            d = parse_date(text(info[0])) if info else None
            if not (link and title and d):
                continue
            m1, d1, m2, d2 = d
            if not prev and m1 < 7:    # list opens in Jan-Jun, which (as of Nov 2026) means 2027
                year = 2027
            elif m1 < prev - 2:        # wrapped into the next year
                year += 1
            prev = m1
            ey = year + (1 if m2 < m1 else 0)
            if (year, m1) > (2027, 7):
                done = True
                break
            if (year, m1) not in ((2027, 6), (2027, 7)):
                continue
            ages = next((x for x in lst if re.search(r'\d+U', x)), '')
            loc = next((x for x in lst if re.search(r',\s*[A-Z]{2}$', x)), '')
            director = lst[-1] if lst and lst[-1] not in (ages, loc) else ''
            rows.append(dict(site=st, name=text(title[1]), start=f'{year}-{m1:02}-{d1:02}', end=f'{ey}-{m2:02}-{d2:02}',
                             ages=ages, loc=loc, director=director, link=link[1]))
        if done or 'class="next page-numbers"' not in h:
            break
        page += 1
        time.sleep(0.5)
    print(f'{st}: {len(rows)} Jun-Jul events ({page} pages)', file=sys.stderr)
    return rows


with ThreadPoolExecutor(6) as ex:
    allrows = [r for rs in ex.map(scrape, STATES) for r in rs]
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(allrows[0].keys()))
    w.writeheader()
    w.writerows(allrows)
print('total', len(allrows), file=sys.stderr)
