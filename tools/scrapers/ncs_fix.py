"""Clean ncs_draft.csv city labels and names -> ncs_draft2.csv"""
import csv, re
CITY = {'Alburqurque': ('Albuquerque', ''), 'Mather/Woodland': ('Woodland', ''), 'Orange County': ('Irvine', ''),
        'Billy Hebert Stockton': ('Stockton', ''), 'Golden Eagle Park Sparks': ('Sparks', ''),
        'Mather/Billy Hebert': ('Sacramento area', 'Sacramento, CA'), 'Dfw': ('Dallas-Fort Worth area', 'Dallas, TX'),
        'Longview & Kilgore': ('Longview', ''), 'Boise, Meridian': ('Boise', ''), 'bakersfield': ('Bakersfield', ''),
        'Elko, Spring Creek': ('Elko', ''), 'Doc Romeo Park | Las Vegas': ('Las Vegas', ''),
        'Galveston/League City': ('Galveston', ''), 'Bedford, Grapevine': ('Grapevine', ''),
        'Paso Robles-Pismo Beach-San Luis Obispo-Santa Maria': ('San Luis Obispo area', 'San Luis Obispo, CA'),
        'Paso Robles To Santa Maria': ('San Luis Obispo area', 'San Luis Obispo, CA'),
        'San Lusi Obispo-Paso-Pismo-Arroyo Grande-Atascadero': ('San Luis Obispo area', 'San Luis Obispo, CA'),
        'Arroyo Grande-Slo-Sm-Paso': ('San Luis Obispo area', 'San Luis Obispo, CA'), 'Denton': ('Denton', '')}
NAME = [(r'^2 Day Ring in the New Year 2026', '2 Day Ring in the New Year'), (r'LIne drive', 'Line Drive'),
        (r'^7th Annual Sd Mlk', '7th Annual SD MLK'), (r'\s*-\s*\(D1/Open\)', ' (D1/Open)'), (r'^2026 San Diego', 'San Diego'),
        (r'ICE Breaker', 'Ice Breaker'), (r'^Xcs ', 'XCS '), (r' - Hb / Irvine', ''), (r'^"the Challenge"', 'The Challenge'),
        (r'Dfw', 'DFW'), (r' - ALL Turf - ', ' - All Turf - '), (r'Ncs ', 'NCS '), (r'Ws Warm', 'WS Warm'),
        (r'Texas Open Series#', 'Texas Open Series #'), (r'Turntwo', 'TurnTwo'), (r'^"THE Show"', 'The Show'),
        (r'^2026 NCS (Alabama|Southeast) State', r'2027 NCS \1 State'), (r'^2026 NCS Southeast D3', '2027 NCS Southeast D3'),
        (r'12open', '12U Open'), (r' \(Ncs Sd\)', ''), (r' 3x Points Las Vegas, NV', ''), (r'Az May', 'AZ May'),
        (r'Mid- South Mayham', 'Mid-South Mayhem'), (r'Idaho Classsic', 'Idaho Classic'),
        (r'Swing n\' Cruz New!+', "Swing n' Cruz"), (r' \(Friday - Pool games.*?\)', ''), (r'—', '-'),
        (r'Spring Training Classic l ', 'Spring Training Classic I '), (r'Spring Training Classic ll ', 'Spring Training Classic II ')]
rows = []
for r in csv.DictReader(open('ncs_draft.csv', encoding='utf-8')):
    if 'Ultimate' in r['name']:
        continue                      # already in DB as 'Ultimate Baseball World Series (NCS)'
    r['city'], r['geo'] = CITY.get(r['city'], (r['city'], r['geo']))
    for a, b in NAME:
        r['name'] = re.sub(a, b, r['name'])
    rows.append(r)
# same name, different week -> keep; same name + date already handled
w = csv.DictWriter(open('ncs_draft2.csv', 'w', newline='', encoding='utf-8'), fieldnames=list(rows[0]))
w.writeheader(); w.writerows(rows)
for r in rows: print(r['start_date'], r['city'], r['state'], '|', r['name'])
