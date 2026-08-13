import json
import os
import sys
from datetime import date

import cherrypy
import markdown as md_lib
from jinja2 import Environment, FileSystemLoader

import auth
import oauth_google
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
jinja.globals['get_csrf_token'] = auth.get_csrf_token


def render(template_name, **ctx):
    ctx.setdefault('user', auth.current_user())
    tmpl = jinja.get_template(template_name)
    return tmpl.render(**ctx)


def google_redirect_uri():
    base_url = os.environ.get('APP_BASE_URL', 'http://localhost:8080')
    return base_url.rstrip('/') + '/auth/google/callback'


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
        return render('post_list.html', posts=posts, category=category)

    @cherrypy.expose
    def default(self, slug):
        post = fetch_post(slug)
        if not post:
            raise cherrypy.HTTPError(404)
        body_html = md_lib.markdown(post['body'] or '', extensions=['extra'])
        return render('post.html', post=post, body_html=body_html)


class Complexes:
    @cherrypy.expose
    def index(self):
        complexes = fetch_complexes()
        return render('complex_list.html', complexes=complexes)

    @cherrypy.expose
    def default(self, slug):
        complex_ = fetch_complex(slug)
        if not complex_:
            raise cherrypy.HTTPError(404)
        body_html = md_lib.markdown(complex_['body'] or '', extensions=['extra'])
        return render('complex.html', complex=complex_, body_html=body_html)


class App:
    @cherrypy.expose
    def index(self, age='14'):
        return self.map(age=age)

    @cherrypy.expose
    def map(self, age='14'):
        try:
            age = int(age)
        except ValueError:
            age = 14
        events = fetch_events(age)
        return render(
            'map.html',
            events_json=json.dumps(events),
            org_meta_json=json.dumps(ORG_META),
            org_meta=ORG_META,
            months=MONTHS,
            age=age,
            total=len(events),
        )

    @cherrypy.expose
    def register(self, email=None, password=None, name=None, username=None, csrf_token=None, next='/'):
        error = None
        if cherrypy.request.method == 'POST':
            auth.check_csrf(csrf_token)
            if not email or not password or not name or not username:
                error = 'All fields are required.'
            elif len(password) < 8:
                error = 'Password must be at least 8 characters.'
            elif not auth.is_valid_username(username):
                error = 'Username must be 3-20 characters: letters, numbers, or underscores.'
            elif auth.get_user_by_username(username):
                error = 'That username is already taken.'
            elif auth.get_user_by_email(email):
                error = 'An account with that email already exists.'
            if not error:
                user = auth.create_user(email, password, name, username)
                auth.login_user(user)
                token = auth.create_verification_token(user['id'])
                verify_link = cherrypy.url(f'/verify-email?token={token}')
                return render('verify_pending.html', verify_link=verify_link, next=next)
        return render('register.html', error=error, email=email, name=name,
                       username=username, next=next, csrf_token=auth.get_csrf_token())

    @cherrypy.expose
    def verify_email(self, token=None):
        ok = auth.verify_email_token(token)
        return render('verify_result.html', ok=ok)

    @cherrypy.expose
    @auth.require_login
    def resend_verification(self, csrf_token=None):
        auth.check_csrf(csrf_token)
        user = auth.current_user()
        if user['email_verified_at']:
            raise cherrypy.HTTPRedirect('/')
        token = auth.create_verification_token(user['id'])
        verify_link = cherrypy.url(f'/verify-email?token={token}')
        return render('verify_pending.html', verify_link=verify_link, next='/')

    @cherrypy.expose
    def login(self, email=None, password=None, csrf_token=None, next='/'):
        error = None
        if cherrypy.request.method == 'POST':
            auth.check_csrf(csrf_token)
            user = auth.get_user_by_email(email) if email else None
            if not user or not auth.verify_password(password or '', user['password_hash']):
                error = 'Invalid email or password.'
            else:
                auth.login_user(user)
                raise cherrypy.HTTPRedirect(next or '/')
        return render('login.html', error=error, email=email, next=next,
                       csrf_token=auth.get_csrf_token())

    @cherrypy.expose
    def logout(self, csrf_token=None):
        auth.check_csrf(csrf_token)
        auth.logout_user()
        raise cherrypy.HTTPRedirect('/')


class GoogleAuth:
    @cherrypy.expose
    def index(self, next='/'):
        redirect_uri = google_redirect_uri()
        uri, state = oauth_google.get_google_auth_url(redirect_uri)
        cherrypy.session['oauth_state'] = state
        cherrypy.session['oauth_next'] = next
        raise cherrypy.HTTPRedirect(uri)

    @cherrypy.expose
    def callback(self, code=None, state=None, error=None):
        if error or not code:
            raise cherrypy.HTTPRedirect('/login')
        expected_state = cherrypy.session.get('oauth_state')
        if not expected_state or state != expected_state:
            raise cherrypy.HTTPError(400, 'Invalid OAuth state')
        redirect_uri = google_redirect_uri()
        authorization_response = cherrypy.url(qs=cherrypy.request.query_string)
        google_user = oauth_google.fetch_google_user(redirect_uri, authorization_response, state)
        user = auth.upsert_google_user(google_user['sub'], google_user['email'], google_user['name'])
        auth.login_user(user)
        next_url = cherrypy.session.pop('oauth_next', None) or '/'
        raise cherrypy.HTTPRedirect(next_url)


class Admin:
    @cherrypy.expose
    @auth.require_admin
    def index(self):
        return render('admin.html')


if __name__ == '__main__':
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8080,
        'tools.sessions.on': True,
        'tools.sessions.storage_type': 'ram',
        'tools.sessions.timeout': 60 * 24,
    })
    app = App()
    app.admin = Admin()
    cherrypy.tree.mount(app, '/', {
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': os.path.join(os.path.dirname(__file__), 'static'),
        }
    })
    cherrypy.tree.mount(GoogleAuth(), '/auth/google')
    cherrypy.engine.start()
    cherrypy.engine.block()
