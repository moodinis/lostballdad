"""Insert tournaments from a CSV into the DB, skipping rows already present (same name + start_date).

Usage: python tools/import_csv.py draft_geo.csv

Columns: name,organizer,city,state,start_date,end_date,start_age,end_age,link,lat,lng
  organizer must match organizers.name exactly (e.g. "USSSA", "Perfect Game", "Other").
  Extra columns are ignored. Uses DB credentials from .env via db.py.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from db import get_conn  # noqa: E402

path = sys.argv[1]
conn = get_conn()
cur = conn.cursor()
cur.execute('SELECT name, id FROM organizers')
org_ids = dict(cur.fetchall())

inserted, skipped = [], []
with open(path, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        cur.execute('SELECT id FROM tournaments WHERE name=%s AND start_date=%s', (r['name'], r['start_date']))
        if cur.fetchone():
            skipped.append(r['name'])
            continue
        cur.execute(
            '''INSERT INTO tournaments
               (name, organizer_id, city, state, start_date, end_date, start_age, end_age, link, lat, lng)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (r['name'], org_ids[r['organizer']], r['city'], r['state'], r['start_date'], r['end_date'],
             int(r['start_age']), int(r['end_age']), r['link'], r['lat'], r['lng']))
        inserted.append(cur.lastrowid)

conn.commit()
print(f'inserted {len(inserted)} (ids {min(inserted)}-{max(inserted)})' if inserted else 'inserted 0')
print(f'skipped {len(skipped)} duplicates: {skipped}')
