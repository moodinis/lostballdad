import json
import os
import sys
from datetime import date

import cherrypy
from jinja2 import Environment, FileSystemLoader

from db import get_conn

ORG_META = {
    'pg':    {'label': 'Perfect Game',          'color': '#1F3A5F'},
    'usssa': {'label': 'USSSA',                 'color': '#BC5B39'},
    'tc':    {'label': 'Triple Crown Sports',   'color': '#2F6F4E'},
    'gt':    {'label': 'Gametime Tournaments',  'color': '#EAB308'},
    'gsc':   {'label': 'Genesis Sports Complex','color': '#EA580C'},
    'kcs':   {'label': 'KC Sports',             'color': '#7C3AED'},
    'sa':    {'label': 'Sports America',        'color': '#0891B2'},
    'ft':    {'label': 'Five Tool',             'color': '#DC2626'},
}

ORG_CODES = {
    'Perfect Game':          'pg',
    'USSSA':                 'usssa',
    'Triple Crown Sports':   'tc',
    'Gametime Tournaments':  'gt',
    'Genesis Sports Complex':'gsc',
    'KC Sports':             'kcs',
    'Sports America':        'sa',
    'Five Tool':             'ft',
}

MONTHS = ['Aug', 'Sep', 'Oct', 'Nov', 'Dec']
MONTH_ABBR = {8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}

jinja = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))


def fetch_events(age=14):
    fmt = '%b %#d' if sys.platform == 'win32' else '%b %-d'
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.name, o.name, t.city, t.state,
               t.start_date, t.end_date, t.link, t.lat, t.lng
        FROM tournaments t
        JOIN organizers o ON t.organizer_id = o.id
        WHERE t.start_age <= %s AND t.end_age >= %s
          AND MONTH(t.start_date) BETWEEN 8 AND 12
        ORDER BY t.start_date
    """, (age, age))
    events = []
    for name, org_name, city, state, start, end, link, lat, lng in cur.fetchall():
        org = ORG_CODES.get(org_name, 'pg')
        month = MONTH_ABBR.get(start.month, '')
        if start == end:
            dates = f"{start.strftime(fmt)}, {start.year}"
        elif start.month == end.month:
            dates = f"{start.strftime(fmt)}–{end.day}, {end.year}"
        else:
            dates = f"{start.strftime(fmt)}–{end.strftime(fmt)}, {end.year}"
        events.append({
            'org': org, 'month': month, 'name': name,
            'city': city, 'state': state, 'dates': dates,
            'link': link, 'lat': float(lat), 'lng': float(lng),
        })
    cur.close()
    conn.close()
    return events


class App:
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect('/map')

    @cherrypy.expose
    def map(self, age='14'):
        try:
            age = int(age)
        except ValueError:
            age = 14
        events = fetch_events(age)
        tmpl = jinja.get_template('map.html')
        return tmpl.render(
            events_json=json.dumps(events),
            org_meta_json=json.dumps(ORG_META),
            org_meta=ORG_META,
            months=MONTHS,
            age=age,
            total=len(events),
        )


if __name__ == '__main__':
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8080,
    })
    cherrypy.quickstart(App(), '/', {
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': os.path.join(os.path.dirname(__file__), 'static'),
        }
    })
