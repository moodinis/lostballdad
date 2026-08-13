import os

from authlib.integrations.requests_client import OAuth2Session

AUTHORIZATION_ENDPOINT = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'
USERINFO_ENDPOINT = 'https://openidconnect.googleapis.com/v1/userinfo'
SCOPE = 'openid email profile'


def _client(redirect_uri):
    return OAuth2Session(
        os.environ['GOOGLE_CLIENT_ID'],
        os.environ['GOOGLE_CLIENT_SECRET'],
        scope=SCOPE,
        redirect_uri=redirect_uri,
    )


def get_google_auth_url(redirect_uri):
    client = _client(redirect_uri)
    uri, state = client.create_authorization_url(AUTHORIZATION_ENDPOINT)
    return uri, state


def fetch_google_user(redirect_uri, authorization_response, state):
    client = _client(redirect_uri)
    client.fetch_token(
        TOKEN_ENDPOINT,
        authorization_response=authorization_response,
        state=state,
    )
    resp = client.get(USERINFO_ENDPOINT)
    resp.raise_for_status()
    data = resp.json()
    return {
        'sub': data['sub'],
        'email': data['email'],
        'name': data.get('name') or data['email'],
    }
