"""Exercise real local-AI grading through Flask using disposable data only."""
import json
from pathlib import Path
import runpy
import tempfile

from lab.app import create_app
from lab.curriculum import MODULES
from lab.db import get_db
from lab.grading import expected_choice

fixtures = runpy.run_path(str(Path(__file__).with_name('check-reviewer.py')))
with tempfile.TemporaryDirectory(prefix='reviewer-flow-') as directory:
    app = create_app({'TESTING': True, 'DATA_DIR': directory,
                      'DATABASE': directory + '/lab.sqlite3', 'REVIEW_MODE': 'local-ai',
                      'REVIEW_URL': 'http://ollama:11434', 'REVIEW_MODEL': fixtures['MODEL']})
    client = app.test_client()
    def post(path, data=None):
        with client.session_transaction() as session:
            csrf = session.get('csrf', '')
        return client.post(path, data={'csrf': csrf, **(data or {})})
    client.get('/setup')
    with app.app_context():
        token = get_db().execute("SELECT value FROM settings WHERE key='setup_token'").fetchone()[0]
    password = 'temporary isolated validation password'
    assert post('/setup', {'token': token, 'password': password, 'confirm': password}).status_code == 303
    client.get('/login')
    assert post('/login', {'password': password}).status_code == 303
    post('/learn/42/read')
    module = MODULES[42]
    quiz = {**module, 'id': f"understanding:42:{module['teaching']['version']}", 'probes': module['understanding']}
    assert post('/practice/42/submit', fixtures['payload']).status_code == 403
    post('/learn/42/check', {p['key']: expected_choice(quiz, app.secret_key, p['key']) for p in quiz['probes']})
    post('/notebook', {'module_id': '42', 'kind': 'observation', **fixtures['note']})
    with app.app_context():
        note_id = get_db().execute('SELECT max(id) FROM notes').fetchone()[0]
    data = {**fixtures['payload'], 'confidence': '80', 'reviewed': 'yes', 'note_id': str(note_id),
            **{p['key']: expected_choice(MODULES[42], app.secret_key, p['key']) for p in MODULES[42]['probes']}}
    wrong = fixtures['CASES'][1][2]['reasoning']
    response = post('/practice/42/submit', {**data, 'reasoning': wrong})
    assert b'Build the prerequisite model' in client.get('/practice/1').data
    response = post('/checkpoint/42/submit', data)
    assert response.status_code == 303
    assert b'Build the prerequisite model' in client.get('/practice/1').data
    with app.app_context():
        result = json.loads(get_db().execute('SELECT result FROM attempts ORDER BY id DESC LIMIT 1').fetchone()[0])
        assert not result['passed'] and result['semantic']['reasoning'] < 2
    response = post('/practice/42/submit', data)
    response = post('/checkpoint/42/submit', data)
    page = client.get(response.location)
    assert page.status_code == 200 and b'Your model holds for this case.' in page.data
    assert b'Each field was assessed independently' in page.data
    assert b'Build the prerequisite model' not in client.get('/practice/1').data
    with app.app_context():
        result = json.loads(get_db().execute('SELECT result FROM attempts ORDER BY id DESC LIMIT 1').fetchone()[0])
        assert result['passed'] and result['semantic']['rubric_version'] == 'independent-fields-v4-teachback'
        assert all(passage in data['reflection'] for passage in result['semantic']['quotes']['transfer'].splitlines())
print('Real-model application flow passed: wrong reasoning held the gate; corrected reasoning rendered cited feedback and unlocked the next module. Disposable database only.')
