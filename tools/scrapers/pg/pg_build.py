"""pg_groups_all.json -> pg_draft.csv (organizer Perfect Game). Skips leagues/multi-week, <12U, non-US, and rows already in the DB."""
import collections, csv, json, os, re, sys
from datetime import date, datetime
os.chdir('/home/cctom/projects/tourneysv2'); sys.path.insert(0, '.'); import db
os.chdir(os.path.dirname(os.path.abspath(__file__)))
conn = db.get_conn(); cur = conn.cursor()
cur.execute("select name, state, start_date, link from tournaments where start_date between '2027-01-01' and '2027-08-15'")
existing = cur.fetchall()
have_gid = {m[1] for *_, l in existing for m in [re.search(r'gid=(\d+)', l or '')] if m}
norm = lambda s: re.sub(r'[^a-z0-9]', '', re.sub(r'^2027 |\(.*?\)|pg |perfect game', '', s.lower()))
have_key = {(st, d, norm(n)) for n, st, d, _ in existing}
US = set('AK AL AR AZ CA CO CT DE FL GA HI IA ID IL IN KS KY LA MA MD ME MI MN MO MS MT NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT WA WI WV WY'.split())
NAMES = {'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut',
         'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'IA': 'Iowa', 'ID': 'Idaho', 'IL': 'Illinois',
         'IN': 'Indiana', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'MA': 'Massachusetts', 'MD': 'Maryland',
         'ME': 'Maine', 'MI': 'Michigan', 'MN': 'Minnesota', 'MO': 'Missouri', 'MS': 'Mississippi', 'NC': 'North Carolina',
         'ND': 'North Dakota', 'NE': 'Nebraska', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NV': 'Nevada',
         'NY': 'New York', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island',
         'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VA': 'Virginia',
         'VT': 'Vermont', 'WA': 'Washington', 'WI': 'Wisconsin', 'WV': 'West Virginia'}


FIX = {'Alabama': ('Hoover', ''), 'North Alabama HS': ('North Alabama area', 'Decatur, AL'), 'Morgan County': ('Decatur', ''),
       'Flint': ('Moulton', ''), 'Huntsville Kiwanis': ('Huntsville', ''), 'Huntsville Sportsplex': ('Huntsville', ''),
       'Huntsville Sportspex Moulton': ('Huntsville', ''), 'Florence Sportsplex': ('Florence', ''),
       'Keizer Little League': ('Keizer', ''), 'Gill Stadium Turf Field': ('Manchester', ''),
       'Greater Lawrence Technical School': ('Andover', ''), 'Greater Seattle': ('Seattle area', 'Seattle, WA'),
       'Northeast': ('Northeast Georgia', 'Gainesville, GA'), 'No Offseason Sports': ('Pittsburgh', ''),
       'Prince George County': ("Prince George's County", 'Upper Marlboro, MD'), 'Long Island': ('Long Island', 'Hauppauge, NY'),
       'South Jersey': ('South Jersey', 'Cherry Hill, NJ'), 'Dfw': ('Dallas-Fort Worth area', 'Dallas, TX'),
       'Pemboke Pines': ('Pembroke Pines', ''), 'Central': ('Jackson area', 'Jackson, MS'), "D'iberville": ("D'Iberville", ''),
       'Ft Wayne': ('Fort Wayne', ''), 'Various Parks': ('St. Augustine', ''), 'Connecticut': ('Connecticut', 'Hartford, CT')}

VENUE = {'Bill Noble Park': 'Gardendale', 'Clarence E. Morgan': 'Savannah', "DICK's Sporting Goods Park": 'Marietta',
         'DICK’S Sporting Goods Park': 'Marietta', 'Hoover Met': 'Hoover', 'North Alabama HS': 'North Alabama HS',
         'Southside Sports Complex': 'Lake City', 'St. Johns County': 'St. Augustine'}


def clean_loc(loc, st):
    """PG locations are free text ('Mesa, Arizona', 'Sanford', 'HOUSTON, TEXAS', 'Fairfax (VA) | Newark | ...');
    the state comes from the per-state search. Returns (city, state, geo)."""
    sites = [x.strip() for x in loc.split('|') if x.strip()]
    if not sites:
        return None
    site = next((x for x in sites if re.search(r'\(%s\)' % st, x) or NAMES[st].lower() in x.lower()), sites[0])
    c = re.sub(r'\s*\([A-Z]{2}\)', '', site)
    c = re.sub(r'^.* - (?=[A-Z][a-z]+(?: [A-Z][a-z]+)?$)', '', c)                        # 'Venue - City'
    c = re.sub(r'(?i)[,\s]+(%s|%s)\b.*$' % (re.escape(NAMES[st]), st), '', c)           # trailing state (+ venue)
    c = re.sub(r'(?i)\s*(and|&|\+)?\s*(the\s+)?surrounding (areas?|fields|facilities).*$|\s+(metro\s+)?area$|\s+metro$', '', c)
    c = re.split(r'\s*(?:/|,| & | and )\s*', c.strip(' ,-'))[0].strip()
    if not c:
        return None
    c = c.title() if c.isupper() or c.islower() else c
    for key, val in VENUE.items():
        if key.lower() in site.lower():
            c = val; break
    city, geo = FIX.get(c, (c, ''))
    if city in ('South Jersey',):
        return (city, 'NJ', geo)
    if city in ('Long Island',):
        return (city, 'NY', geo)
    return (city, st, geo)


out, skipped = [], collections.Counter()
for g in json.load(open('pg_groups_all.json')):
    m = re.match(r'(\w{3}) (\d+)(?:-(?:(\w{3}) )?(\d+))?$', g['dates'])
    if not m:
        skipped['bad date'] += 1; continue
    s = datetime.strptime(f'{m[1]} {m[2]} 2027', '%b %d %Y').date()
    e = datetime.strptime(f'{m[3] or m[1]} {m[4] or m[2]} 2027', '%b %d %Y').date()
    ages = [int(a) for a in re.findall(r'(\d+)U', g['ages'])]
    lm = clean_loc(g['loc'], g['state_q'])
    why = ('not Jan-Jul' if not date(2027, 1, 1) <= s <= date(2027, 7, 31) else
           'league/multi-week' if (e - s).days > 7 or re.search(r'league|season', g['name'], re.I) else
           'no ages' if not ages else '<12U' if max(ages) < 12 else
           'no/foreign location' if not lm or lm[1] not in US else
           'already in DB' if g['gid'] in have_gid or (lm[1], s, norm(g['name'])) in have_key else '')
    if why:
        skipped[why] += 1; continue
    city = lm[0]
    if re.search(r'\bTest\b', g['name']):
        skipped['test event'] += 1; continue
    city = city.title() if city.isupper() or city.islower() else city
    out.append(dict(name=re.sub(r'\s+', ' ', g['name']).strip(), organizer='Perfect Game', city=city, state=lm[1],
                    start_date=s, end_date=e, start_age=min(ages), end_age=max(ages),
                    link=f"https://www.perfectgame.org/Schedule/GroupedEvents.aspx?gid={g['gid']}", geo=lm[2]))
dupes = collections.Counter((o['name'], o['start_date']) for o in out)
for o in out:
    if dupes[(o['name'], o['start_date'])] > 1:
        o['name'] += f" ({o['city']})"
w = csv.DictWriter(open('pg_draft.csv', 'w', newline='', encoding='utf-8'), fieldnames=list(out[0]))
w.writeheader(); w.writerows(out)
print(len(out), 'rows;', dict(skipped)); print(collections.Counter(o['state'] for o in out).most_common())
