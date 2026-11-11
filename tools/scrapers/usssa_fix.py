"""Map leftover venue/region labels in usssa_draft.csv (usage: usssa_fix.py usssa_draft.csv usssa_draft2.csv) to cities and pin known-bad geocodes."""
import csv, sys
FIX = {
    'Arkansas': ('Little Rock area', 'Little Rock, AR'), 'Northwest Arkansas': ('Northwest Arkansas', 'Springdale, AR'),
    'Bryan, TX': ('Bryan', ''), 'DFW Metroplex': ('Dallas-Fort Worth area', 'Dallas, TX'), 'Etown': ('Elizabethtown', ''),
    'Farmington Hill': ('Farmington Hills', ''), 'Fort Wayne-World Baseball Academy': ('Fort Wayne', ''),
    'Grand Park': ('Westfield', ''), 'Westfield Grand Park': ('Westfield', ''),
    'Indy Sports Park (ALL TURF)': ('Indianapolis', ''), 'Noblesville & ISP (All Turf)': ('Noblesville', ''),
    'Lutz Complex Arvada': ('Arvada', ''), 'Macomb Corners': ('Macomb', ''), 'New Smyrna': ('New Smyrna Beach', ''),
    'Space Coast Complex': ('Viera', ''), 'Martinsville-G.Wood-Mooresville': ('Martinsville', ''),
}
PIN = {('Marion', 'IL'): '37.7306;-88.9331', ('Seward', 'NE'): '40.9069;-97.0989', ('Burleson', 'TX'): '32.5421;-97.3208',
       ('Westfield', 'IN'): '40.0428;-86.1275'}
src, dst = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(src, encoding='utf-8')))
for r in rows:
    c = r['city']
    if c in FIX:
        r['city'], g = FIX[c]
        r['geo'] = r['geo'] or g
    elif c.startswith(('Indy-', 'Brownsburg-')):
        r['city'] = 'Indianapolis' if c.startswith('Indy') else 'Brownsburg'
    r['geo'] = PIN.get((r['city'], r['state']), r['geo'])
with open(dst, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows))
