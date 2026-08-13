import datetime
import hashlib
import re
import secrets
from functools import wraps

import bcrypt
import cherrypy

from db import get_conn

VERIFICATION_TOKEN_TTL_HOURS = 24
USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]{3,20}$')


def is_valid_username(username):
    return bool(username) and bool(USERNAME_RE.match(username))


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password, password_hash):
    if not password_hash:
        return False
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def _row_to_user(row):
    if not row:
        return None
    id_, email, password_hash, name, username, role, google_id, created_at, email_verified_at = row
    return {
        'id': id_,
        'email': email,
        'password_hash': password_hash,
        'name': name,
        'username': username,
        'role': role,
        'google_id': google_id,
        'created_at': created_at,
        'email_verified_at': email_verified_at,
    }


_USER_COLUMNS = (
    "id, email, password_hash, name, username, role, google_id, created_at, email_verified_at"
)


def get_user_by_id(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT {_USER_COLUMNS} FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return _row_to_user(row)


def get_user_by_email(email):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT {_USER_COLUMNS} FROM users WHERE email = %s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return _row_to_user(row)


def get_user_by_username(username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT {_USER_COLUMNS} FROM users WHERE username = %s", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return _row_to_user(row)


def get_user_by_google_id(google_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT {_USER_COLUMNS} FROM users WHERE google_id = %s", (google_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return _row_to_user(row)


def create_user(email, password, name, username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (email, password_hash, name, username, role) VALUES (%s, %s, %s, %s, 'user')",
        (email, hash_password(password), name, username),
    )
    conn.commit()
    user_id = cur.lastrowid
    cur.close()
    conn.close()
    return get_user_by_id(user_id)


def _generate_username_from_email(email):
    base = re.sub(r'[^a-zA-Z0-9_]', '', email.split('@')[0]).lower()[:20] or 'user'
    conn = get_conn()
    cur = conn.cursor()
    username = base
    suffix = 0
    while True:
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if not cur.fetchone():
            break
        suffix += 1
        username = f"{base}{suffix}"[:20]
    cur.close()
    conn.close()
    return username


def upsert_google_user(google_id, email, name):
    user = get_user_by_google_id(google_id)
    if user:
        return user

    user = get_user_by_email(email)
    conn = get_conn()
    cur = conn.cursor()
    if user:
        cur.execute("UPDATE users SET google_id = %s WHERE id = %s", (google_id, user['id']))
        conn.commit()
        cur.close()
        conn.close()
        return get_user_by_id(user['id'])

    username = _generate_username_from_email(email)
    cur.execute(
        "INSERT INTO users (email, name, username, role, google_id, email_verified_at) "
        "VALUES (%s, %s, %s, 'user', %s, NOW())",
        (email, name, username, google_id),
    )
    conn.commit()
    user_id = cur.lastrowid
    cur.close()
    conn.close()
    return get_user_by_id(user_id)


def create_verification_token(user_id):
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=VERIFICATION_TOKEN_TTL_HOURS)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET verification_token_hash = %s, verification_token_expires_at = %s WHERE id = %s",
        (token_hash, expires_at, user_id),
    )
    conn.commit()
    cur.close()
    conn.close()
    return token


def verify_email_token(token):
    if not token:
        return False
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM users WHERE verification_token_hash = %s "
        "AND verification_token_expires_at > NOW()",
        (token_hash,),
    )
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return False
    user_id = row[0]
    cur.execute(
        "UPDATE users SET email_verified_at = NOW(), verification_token_hash = NULL, "
        "verification_token_expires_at = NULL WHERE id = %s",
        (user_id,),
    )
    conn.commit()
    cur.close()
    conn.close()
    return True


def current_user():
    user_id = cherrypy.session.get('user_id')
    if not user_id:
        return None
    return get_user_by_id(user_id)


def login_user(user):
    cherrypy.session.regenerate()
    cherrypy.session['user_id'] = user['id']


def logout_user():
    cherrypy.session.pop('user_id', None)


def get_csrf_token():
    token = cherrypy.session.get('csrf_token')
    if not token:
        token = secrets.token_hex(16)
        cherrypy.session['csrf_token'] = token
    return token


def check_csrf(token):
    expected = cherrypy.session.get('csrf_token')
    if not expected or not token or not secrets.compare_digest(expected, token):
        raise cherrypy.HTTPError(400, 'Invalid CSRF token')


def require_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user():
            next_url = cherrypy.url(qs=cherrypy.request.query_string)
            raise cherrypy.HTTPRedirect(f'/login?next={next_url}')
        return func(*args, **kwargs)
    return wrapper


def require_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            next_url = cherrypy.url(qs=cherrypy.request.query_string)
            raise cherrypy.HTTPRedirect(f'/login?next={next_url}')
        if user['role'] != 'admin':
            raise cherrypy.HTTPError(403, 'Admin access required')
        return func(*args, **kwargs)
    return wrapper
