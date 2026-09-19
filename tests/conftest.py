import pytest
from lab.app import create_app
from lab.db import get_db

@pytest.fixture
def app(tmp_path):
    return create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'lab.sqlite3'), 'DATA_DIR': str(tmp_path), 'REVIEW_MODE': 'structured'})

@pytest.fixture
def client(app):
    client = app.test_client()
    client.get('/setup')
    with app.app_context():
        token = get_db().execute("SELECT value FROM settings WHERE key='setup_token'").fetchone()[0]
    post(client, '/setup', {'token': token, 'password': 'a long test password', 'confirm': 'a long test password'})
    client.get('/login')
    post(client, '/login', {'password': 'a long test password'})
    return client


def post(client, path, data=None, **kwargs):
    with client.session_transaction() as session:
        csrf = session.get('csrf', '')
    return client.post(path, data={'csrf': csrf, **(data or {})}, **kwargs)
