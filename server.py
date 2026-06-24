import json
import os
import sys
from datetime import date

import cherrypy
import markdown as md_lib
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


def fetch_recent_posts(limit=6):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT title, slug, excerpt, category, published_at
        FROM posts
        WHERE published_at <= NOW()
        ORDER BY published_at DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    posts = []
    for title, slug, excerpt, category, published_at in rows:
        posts.append({
            'title': title,
            'slug': slug,
            'excerpt': excerpt,
            'category': category,
            'published_at': published_at,
        })
    return posts


def fetch_posts(category=None):
    conn = get_conn()
    cur = conn.cursor()
    if category:
        cur.execute("""
            SELECT title, slug, excerpt, category, published_at
            FROM posts
            WHERE published_at <= NOW() AND category = %s
            ORDER BY published_at DESC
        """, (category,))
    else:
        cur.execute("""
            SELECT title, slug, excerpt, category, published_at
            FROM posts
            WHERE published_at <= NOW()
            ORDER BY published_at DESC
        """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    posts = []
    for title, slug, excerpt, category, published_at in rows:
        posts.append({
            'title': title,
            'slug': slug,
            'excerpt': excerpt,
            'category': category,
            'published_at': published_at,
        })
    return posts


def fetch_post(slug):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT title, slug, body, category, published_at
        FROM posts
        WHERE slug = %s AND published_at <= NOW()
    """, (slug,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    title, slug, body, category, published_at = row
    return {
        'title': title,
        'slug': slug,
        'body': body,
        'category': category,
        'published_at': published_at,
    }


def fetch_complexes():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT name, slug, city, state, rating, excerpt
        FROM complexes
        WHERE published_at <= NOW()
        ORDER BY name
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    complexes = []
    for name, slug, city, state, rating, excerpt in rows:
        complexes.append({
            'name': name,
            'slug': slug,
            'city': city,
            'state': state,
            'rating': rating,
            'excerpt': excerpt,
        })
    return complexes


def fetch_complex(slug):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT name, slug, city, state, rating, body, published_at
        FROM complexes
        WHERE slug = %s AND published_at <= NOW()
    """, (slug,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    name, slug, city, state, rating, body, published_at = row
    return {
        'name': name,
        'slug': slug,
        'city': city,
        'state': state,
        'rating': rating,
        'body': body,
        'published_at': published_at,
    }


class Blog:
    @cherrypy.expose
    def index(self, category=None):
        posts = fetch_posts(category)
        tmpl = jinja.get_template('post_list.html')
        return tmpl.render(posts=posts, category=category)

    @cherrypy.expose
    def default(self, slug):
        post = fetch_post(slug)
        if not post:
            raise cherrypy.HTTPError(404)
        body_html = md_lib.markdown(post['body'] or '', extensions=['extra'])
        tmpl = jinja.get_template('post.html')
        return tmpl.render(post=post, body_html=body_html)


class Complexes:
    @cherrypy.expose
    def index(self):
        complexes = fetch_complexes()
        tmpl = jinja.get_template('complex_list.html')
        return tmpl.render(complexes=complexes)

    @cherrypy.expose
    def default(self, slug):
        complex_ = fetch_complex(slug)
        if not complex_:
            raise cherrypy.HTTPError(404)
        body_html = md_lib.markdown(complex_['body'] or '', extensions=['extra'])
        tmpl = jinja.get_template('complex.html')
        return tmpl.render(complex=complex_, body_html=body_html)


class App:
    blog = Blog()
    complexes = Complexes()

    @cherrypy.expose
    def index(self):
        recent_posts = fetch_recent_posts(6)
        tmpl = jinja.get_template('home.html')
        return tmpl.render(recent_posts=recent_posts)

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
