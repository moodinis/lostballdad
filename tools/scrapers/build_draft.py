"""usssa_raw.csv -> usssa_draft.csv in tools/import_csv.py format (name,organizer,city,state,...,link,geo)."""
import collections, csv, re

# loc label (before ", ST") -> (city, state override or None, geo)
CITY = {
    'Scrap Yard': ('Conroe', None, ''), 'MWC': ('Midwest City', None, ''), 'OKC': ('Oklahoma City', None, ''),
    'Kentuckiana': ('Louisville area', None, 'Louisville, KY'),
    'Kentuckiana/Elizabethtown/Frankfort': ('Louisville area', None, 'Louisville, KY'),
    'Greater New Orleans Area': ('New Orleans area', None, 'New Orleans, LA'),
    'Eastern Jackson County': ('Eastern Jackson County', None, 'Blue Springs, MO'),
    'Tri Cities': ('Tri-Cities', None, 'Johnson City, TN'),
    'Sprowls Horizon Park': ('Pinellas Park', None, ''), 'Bob Lewis Park': ('Candler', None, ''),
    'NoCo': ('Northern Colorado', None, 'Fort Collins, CO'),
    'Booombah Sports Complex': ('Sorrento', None, ''), 'Champions Park, Newberry': ('Newberry', None, ''),
    'Space Coast Complex (Viera)': ('Viera', None, ''), 'Freedom Park - Valdosta': ('Valdosta', None, ''),
    'Crownpoint Sports Complex': ('Crown Point', None, ''),
    'Westfield (Grand Park)': ('Westfield', None, ''), 'Westfield-Grand Park': ('Westfield', None, ''),
    'Clearwater/ Tampa Bay area': ('Clearwater', None, ''), 'SOUTH FLORIDA': ('South Florida', None, 'Fort Lauderdale, FL'),
    'Central Arkansas': ('Little Rock area', None, 'Little Rock, AR'), 'TBA': ('Little Rock area', None, 'Little Rock, AR'),
    'Kansas City Metro': ('Kansas City area', None, 'Kansas City, MO'),
    'Liberty, MO / Shawnee, KS': ('Liberty', 'MO', ''), 'Edwardsburg, MI': ('Edwardsburg', 'MI', ''),
    'Clarksville / New Albany / Jeff': ('Clarksville', 'IN', ''),
    'Gilbert, Glendale, Peoria': ('Phoenix area', None, 'Phoenix, AZ'),
    'Glendale, Peoria, Chndler, Mesa, FH': ('Phoenix area', None, 'Phoenix, AZ'),
    'Glendale, Peoria, FH': ('Phoenix area', None, 'Phoenix, AZ'),
    'Indy': ('Indianapolis', None, ''), 'Indy-Brownsburg-G.Wood-Martinsville': ('Indianapolis', None, ''),
    'Indy-Brownsburg-Mooreville': ('Indianapolis', None, ''), 'Noblesville-Indy All TURF': ('Noblesville', None, ''),
    'Martinsville-Mooresville': ('Martinsville', None, ''), 'Brownsburg TURF': ('Brownsburg', None, ''),
    'Evansville/Henderson (all turf)': ('Evansville', None, ''),
    'Omaha Metro': ('Omaha', None, ''), 'Omaha/CB': ('Omaha', None, ''), 'LaVista': ('La Vista', None, ''),
    'Nashville Area': ('Nashville', None, ''), 'Ruston | Monroe': ('Ruston', None, ''),
    'New Smyrna': ('New Smyrna Beach', None, ''), 'NEW SMYRNA/ORMOND': ('New Smyrna Beach', None, ''),
    'Ft Smith': ('Fort Smith', None, ''), 'Port St Lucie': ('Port St. Lucie', None, ''), 'Deforest': ('DeForest', None, ''),
    'Coralville/CR Corridor': ('Coralville', None, ''), 'Iowa City/CR Corridor': ('Iowa City', None, ''),
    # same-named towns Nominatim resolves to the wrong place
    'Marion|IA': ('Marion', None, '42.0342;-91.5977'), 'Decatur|IN': ('Decatur', None, '40.8306;-84.9291'),
}
KEEP_CAPS = {'USSSA', 'NIT', 'NCTB', 'KCS', 'WBA', 'MWC', 'OKC', 'GNO', 'BCS', 'AAU', 'NFFF', 'II', 'III', 'IV',
             'CS', 'UA', 'CTS', 'PAP', 'MLB', 'A', 'AA', 'AAA', 'GG', 'JP2', 'KC', 'NV', 'TBA', 'CFL', 'BLC', '3UP', '3DOWN'}
SMALL = {'OF', 'THE', 'TO', 'ON', 'IN', 'BY', 'FOR', 'AND', 'AT'}


def fix_caps(name):
    """Title-case shouted words. In an all-caps name every word is fair game; in a mixed name only words of 4+
    letters, since short caps words there (CS, PG, DFW) are usually acronyms."""
    shouting = sum(c.isupper() for c in name) > 0.5 * sum(c.isalpha() for c in name)

    def w(m):
        t = m.group(0)
        if t in KEEP_CAPS or re.fullmatch(r'\d*GG|\d+[A-Z]?U', t):
            return t
        if re.fullmatch(r'\d+(ST|ND|RD|TH|LB)', t):
            return t.lower()
        if not shouting and len(re.sub(r'\W', '', t)) < 4:
            return t
        if t in SMALL and m.start() > 0:
            return t.lower()
        return t[0] + t[1:].lower() if t[0].isalpha() else t.lower()

    name = re.sub(r'\s+', ' ', name).strip()
    return re.sub(r"\b[A-Z0-9][A-Z0-9'’]*[A-Z]\b|\b[A-Z]\b", w, name)


rows = list(csv.DictReader(open('usssa_raw.csv', encoding='utf-8')))
out, skipped = [], []
for r in rows:
    m = re.match(r'(\d+)U\s*-\s*(\d+)U', r['ages'])
    a1, a2 = int(m[1]), int(m[2])
    if a2 < 12:
        skipped.append(f"<12U: {r['name']} ({r['ages']})")
        continue
    label, st = re.match(r'(.*),\s*([A-Z]{2})$', r['loc']).groups()
    key = label if label in CITY else f'{label}|{st}'
    if key in CITY:
        city, st2, geo = CITY[key]
        st = st2 or st
    else:
        city, geo = re.split(r'\s*[/|]\s*', label)[0], ''
        city = city.title() if city.isupper() else city
    d = r['director'].lower()
    org = ('Sports America' if 'sports america' in d else
           'KC Sports' if 'fortuna' in d or 'kc sports' in d or 'kcs' in d.split() else 'USSSA')
    out.append(dict(name=fix_caps(r['name']), organizer=org, city=city, state=st, start_date=r['start'],
                    end_date=r['end'], start_age=a1, end_age=a2, link=r['link'], geo=geo))

# disambiguate shared name + start date (within the batch)
dupes = collections.Counter((o['name'], o['start_date']) for o in out)
for o in out:
    if dupes[(o['name'], o['start_date'])] > 1:
        o['name'] += f" ({o['city']})"

with open('usssa_draft.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)
print(len(out), 'rows;', collections.Counter(o['organizer'] for o in out))
print('\n'.join(skipped))
print('renamed dupes:', [o['name'] for o in out if dupes[(o['name'].rsplit(' (', 1)[0], o['start_date'])] > 1])
