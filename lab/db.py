import sqlite3
from flask import current_app, g

SCHEMA = '''
CREATE TABLE IF NOT EXISTS understanding (module_id INTEGER NOT NULL, version TEXT NOT NULL, payload TEXT NOT NULL, result TEXT NOT NULL, passed INTEGER NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(module_id,version));
CREATE TABLE IF NOT EXISTS practice_runs (id INTEGER PRIMARY KEY, module_id INTEGER NOT NULL, version TEXT NOT NULL, payload TEXT NOT NULL, result TEXT NOT NULL, passed INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS practice_module ON practice_runs(module_id,id DESC);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS account (id INTEGER PRIMARY KEY CHECK(id=1), password_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS login_failures (address TEXT PRIMARY KEY, count INTEGER NOT NULL, started REAL NOT NULL);
CREATE TABLE IF NOT EXISTS reading (module_id INTEGER PRIMARY KEY, version TEXT NOT NULL, read_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, module_id INTEGER NOT NULL, kind TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS attempts (id INTEGER PRIMARY KEY, module_id INTEGER NOT NULL, version TEXT NOT NULL, payload TEXT NOT NULL, result TEXT NOT NULL, notebook_snapshot TEXT NOT NULL, passed INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS drafts (module_id INTEGER PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS attempts_module ON attempts(module_id, id DESC);
CREATE TABLE IF NOT EXISTS topic_notes (module_id INTEGER NOT NULL, topic TEXT NOT NULL, explanation TEXT NOT NULL, evidence TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(module_id, topic));
'''

def connect(path):
    conn = sqlite3.connect(path, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=15000')
    return conn


def get_db():
    if 'db' not in g:
        g.db = connect(current_app.config['DATABASE'])
    return g.db


def close_db(_error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
