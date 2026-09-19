import json
import pytest
from lab.app import create_app
from lab.catalog import ORDER
from lab.curriculum import MODULES
from lab.db import get_db
from lab.grading import choices, evaluate, expected_choice
from lab.reviewer import ReviewUnavailable, validate_endpoint
from lab.simulations import integer_model, modbus_model, tank_model
from conftest import post

RECORD = {
    'hypothesis': 'I predict the isolated synthetic lab is authorized because its assets remain inside the explicitly stated experimental boundary.',
    'reasoning': 'The permitted scope includes synthetic assets only so the isolated simulation fits both the authorization and physical separation requirements.',
    'observation': 'The artifact states that lab B has no physical input or output and uses an internal network with a snapshot.',
    'reflection': 'If a real actuator were connected I would stop because the original authorization and physical safety assumptions would no longer apply.',
    'workflow': 'Isolation limits where experimental effects travel while authorization specifies permitted actions. The artifact gives B synthetic assets and no physical I/O, so it fits the boundary. Adding an actuator would violate that assumption; stop and reassess permission and physical safeguards before proceeding.',
    'confidence': '80', 'reviewed': 'yes',
}
NOTE = {'body': 'The synthetic environment separates the experiment from physical equipment, but attaching an actuator would invalidate that safety boundary.', 'title': 'Boundary observations'}


def submission(module, secret):
    return {**RECORD, 'answer': module['answers'][0], **{p['key']: expected_choice(module, secret, p['key']) for p in module['probes']}}


def prepare(client, app, number=42):
    post(client, f'/learn/{number}/read')
    module = MODULES[number]
    quiz = {**module, 'id': f"understanding:{number}:{module['teaching']['version']}", 'probes': module['understanding']}
    post(client, f'/learn/{number}/check', {p['key']: expected_choice(quiz, app.secret_key, p['key']) for p in quiz['probes']})
    assert post(client, f'/practice/{number}/submit', submission(module, app.secret_key)).status_code == 303
    post(client, '/notebook', {'module_id': str(number), 'kind': 'observation', **NOTE})
    with app.app_context():
        note_id = get_db().execute('SELECT max(id) FROM notes').fetchone()[0]
    return {**submission(MODULES[number], app.secret_key), 'note_id': str(note_id)}


def test_all_subjects_have_real_cases_and_prerequisites():
    assert set(MODULES) == set(range(1, 43))
    assert len({m['artifact'] for m in MODULES.values()}) == 42
    assert sum(len(m['topics']) for m in MODULES.values()) == 915
    for index, number in enumerate(ORDER):
        module = MODULES[number]
        assert len(module['lesson']) >= 3
        assert len(module['resources']) >= 2
        assert all(url.startswith('https://') for _, url in module['resources'])
        assert all(len(probe['options']) == 3 for probe in module['probes'])
        assert module['prerequisites'] == ORDER[max(index - 1, 0):index]


@pytest.mark.parametrize('dimension', ['model','evidence','transfer'])
def test_correct_result_cannot_mask_wrong_reasoning(dimension):
    module = MODULES[1]
    data = submission(module, 'secret')
    data[dimension] = 'wrong'
    result = evaluate(module, data, 'secret', NOTE)
    assert not result['passed']
    assert result['state'] == 'revise_model'
    assert next(check for check in result['checks'] if check['key'] == 'outcome')['passed']
    assert 'High confidence' in result['calibration']


def test_nonsense_text_is_not_claimed_to_be_semantically_graded():
    module = MODULES[1]
    result = evaluate(module, submission(module, 'secret'), 'secret', NOTE)
    assert result['passed']
    assert 'not understood by an AI' in result['assessment_scope']
    for field in ('hypothesis','reasoning','observation','reflection','workflow'):
        data = submission(module, 'secret')
        data[field] = 'yes yes yes yes yes yes yes yes yes yes yes yes'
        assert not evaluate(module, data, 'secret', NOTE)['passed']


def test_choice_ids_do_not_reveal_answers():
    a, b = choices(MODULES[2], 'first'), choices(MODULES[2], 'second')
    assert a != b
    assert all(len(option['value']) == 24 for probe in a for option in probe['options'])
    assert set(option['label'] for option in a[0]['options']) == set(MODULES[2]['probes'][0]['options'])


def test_ascii_result_preserves_case():
    data = submission(MODULES[11], 'secret')
    assert evaluate(MODULES[11], data, 'secret', NOTE)['passed']
    data['answer'] = 'a'
    assert not evaluate(MODULES[11], data, 'secret', NOTE)['passed']


def test_authentication_and_setup_required(app):
    client = app.test_client()
    assert client.get('/export').location.endswith('/setup')
    assert client.get('/').status_code == 302
    assert client.get('/health').json == {'status': 'ok'}
    client.get('/setup')
    response = post(client, '/setup', {'token': 'wrong', 'password': 'password long enough', 'confirm': 'password long enough'})
    assert b'incorrect' in response.data
    with app.app_context():
        assert get_db().execute('SELECT * FROM account').fetchone() is None


def test_csrf_host_origin_and_logout(client):
    assert client.post('/logout').status_code == 403
    assert client.get('/', headers={'Host': 'evil.example'}).status_code == 400
    assert post(client, '/logout', headers={'Origin': 'https://evil.example'}).status_code == 403
    response = client.get('/')
    assert b'Build a model' in response.data
    assert "frame-ancestors 'none'" in response.headers['Content-Security-Policy']
    assert response.headers['Cache-Control'] == 'no-store'
    assert post(client, '/logout').status_code == 303
    assert client.get('/export').location.endswith('/login')


def test_login_throttled(app, client):
    post(client, '/logout')
    client.get('/login')
    for _ in range(8):
        assert post(client, '/login', {'password': 'wrong'}).status_code == 200
    assert post(client, '/login', {'password': 'a long test password'}).status_code == 429


def test_server_side_gate_and_read_requirement(client, app):
    assert post(client, '/practice/1/submit', submission(MODULES[1], app.secret_key)).status_code == 403
    assert post(client, '/practice/1/draft', {}).status_code == 403
    assert post(client, '/practice/42/submit', submission(MODULES[42], app.secret_key)).status_code == 403
    assert b'Build the prerequisite model' in client.get('/practice/1').data
    assert client.get('/learn/1').status_code == 200


def test_pass_unlock_persistence_and_note_snapshot(client, app):
    data = prepare(client, app)
    response = post(client, '/checkpoint/42/submit', data)
    assert response.status_code == 303
    report = client.get(response.location)
    assert b'Your model holds' in report.data
    assert b'Build the prerequisite model' not in client.get('/practice/1').data
    post(client, '/notebook', {'id': data['note_id'], 'module_id': '42', 'kind': 'note', 'title': 'Changed', 'body': 'This new body must not overwrite an old grading snapshot.'})
    with app.app_context():
        row = get_db().execute('SELECT * FROM attempts').fetchone()
        assert json.loads(row['notebook_snapshot'])['body'] == NOTE['body']
        assert row['passed'] == 1
    restarted = create_app({key: app.config[key] for key in ('TESTING','DATABASE','DATA_DIR','REVIEW_MODE')})
    assert restarted.secret_key == app.secret_key
    second = restarted.test_client()
    second.get('/login')
    post(second, '/login', {'password': 'a long test password'})
    assert b'Build the prerequisite model' not in second.get('/practice/1').data


def test_wrong_module_note_does_not_count(client, app):
    data = prepare(client, app)
    with app.app_context(), get_db() as db:
        db.execute('UPDATE notes SET module_id=1 WHERE id=?', (data['note_id'],))
    response = post(client, '/checkpoint/42/submit', data)
    assert b'Revise and retry' in client.get(response.location).data
    assert b'Build the prerequisite model' in client.get('/practice/1').data


def test_failure_history_draft_and_feedback(client, app):
    data = prepare(client, app)
    data['model'] = 'incorrect'
    response = post(client, '/checkpoint/42/submit', data)
    report = client.get(response.location)
    assert b'causal model needs revision' in report.data
    assert b'Revisit this principle' in report.data
    assert b'Build the prerequisite model' in client.get('/practice/1').data
    assert RECORD['hypothesis'].encode() in client.get('/practice/42').data


def test_notes_search_edit_export_escape(client):
    payload = {'module_id': '42', 'kind': 'journal', 'title': '<script>alert(1)</script>', 'body': 'A careful unique observation about local authorization and isolation with enough distinct words for later analysis.'}
    assert post(client, '/notebook', payload).status_code == 303
    response = client.get('/notebook?q=unique')
    assert b'&lt;script&gt;' in response.data and b'<script>alert' not in response.data
    assert b'A careful unique observation' in response.data
    bundle = client.get('/export')
    assert bundle.json['format'] == 'private-lab-export-v1'
    assert 'account' not in bundle.json and 'settings' not in bundle.json
    assert 'attachment;' in bundle.headers['Content-Disposition']
    assert client.get('/notebook?module=999').status_code == 404
    assert client.get('/notebook?q=%27%20OR%201=1--').status_code == 200


def test_topic_research_is_saved_not_mastery(client, app):
    response = post(client, '/learn/2/topic', {'topic': 'Pointers', 'explanation': 'A typed pointer identifies an object location within its lifetime and bounds.', 'evidence': 'GNU C manual: pointers chapter'})
    assert response.status_code == 303
    assert b'GNU C manual' in client.get('/learn/2').data
    assert b'Build the prerequisite model' in client.get('/practice/2').data
    assert post(client, '/learn/2/topic', {'topic': 'invented'}).status_code == 400


@pytest.mark.parametrize('url', ['https://example.com', 'http://8.8.8.8:11434', 'http://evil.example:11434', 'http://user:pass@localhost:11434', 'http://localhost:11434/evil', 'http://169.254.169.254'])
def test_public_or_unsafe_reviewer_endpoints_refused(url):
    with pytest.raises(ValueError):
        validate_endpoint(url)


def test_ai_unavailable_keeps_gate_closed(client, app, monkeypatch):
    data = prepare(client, app)
    app.config['REVIEW_MODE'] = 'local-ai'
    def unavailable(*args):
        raise ReviewUnavailable('Local model is unavailable.')
    monkeypatch.setattr('lab.app.review', unavailable)
    response = post(client, '/checkpoint/42/submit', data)
    assert b'Review pending' in client.get(response.location).data
    assert b'Build the prerequisite model' in client.get('/practice/1').data
    assert b'Local model is unavailable' in client.get(response.location).data


def test_ai_revise_and_pass_require_both_layers(client, app, monkeypatch):
    data = prepare(client, app)
    app.config['REVIEW_MODE'] = 'local-ai'
    verdict = {'passed': False, 'verdict': 'revise', 'feedback': 'Explain the authorization boundary clearly.', 'model': 'test',
               'reasoning': 1, 'evidence': 2, 'transfer': 2, 'notebook': 2,
               'quotes': {'reasoning': data['reasoning'], 'evidence': data['observation'], 'transfer': data['reflection'], 'notebook': NOTE['body']}}
    monkeypatch.setattr('lab.app.review', lambda *args: verdict)
    response = post(client, '/checkpoint/42/submit', data)
    assert b'Revise and retry' in client.get(response.location).data
    assert b'Build the prerequisite model' in client.get('/practice/1').data
    verdict.update(passed=True, verdict='pass', reasoning=2)
    post(client, '/checkpoint/42/submit', data)
    assert b'Build the prerequisite model' not in client.get('/practice/1').data


def test_ai_uncertainty_is_pending_not_a_negative_grade(client, app, monkeypatch):
    data = prepare(client, app)
    app.config['REVIEW_MODE'] = 'local-ai'
    verdict = {'passed': False, 'verdict': 'uncertain', 'feedback': 'I cannot determine correctness.', 'model': 'test',
               'reasoning': 0, 'evidence': 2, 'transfer': 2, 'notebook': 2,
               'quotes': {}}
    monkeypatch.setattr('lab.app.review', lambda *args: verdict)
    response = post(client, '/checkpoint/42/submit', data)
    page = client.get(response.location)
    assert b'Review pending' in page.data
    assert b'Uncertainty is not a finding' in page.data
    assert b'Build the prerequisite model' in client.get('/practice/1').data


def test_integer_simulation_distinguishes_signed_and_unsigned():
    assert integer_model(250, 10, 8)['unsigned_stored'] == 4
    assert integer_model(0, -1, 8)['signed_interpretation'] == -1
    assert integer_model(0, -1, 8)['unsigned_stored'] == 255
    assert integer_model(4660, 0, 16)['little_endian'] == '34 12'
    with pytest.raises(ValueError):
        integer_model(1, 2, 1000000)


def test_tank_latches_and_handles_boundaries():
    rows = tank_model(78, 5, 2, 4, 80)['trace']
    assert rows[0]['level'] == 81
    assert not rows[0]['trip_latched']
    assert all(row['trip_latched'] for row in rows[1:])
    assert rows[-1]['level'] == 75
    assert tank_model(0, 0, 10, 1, 80)['trace'][0]['level'] == 0


def test_modbus_parser_checks_framing_and_range():
    result = modbus_model('00 01 00 00 00 06 01 03 00 10 00 02')
    assert result['quantity'] == 2 and result['start_address'] == 16
    for bad in ('zz', '', '00 01 00 00 00 05 01 03 00 10 00 02', '00 01 00 00 00 06 01 03 FF FF 00 02'):
        with pytest.raises(ValueError):
            modbus_model(bad)


def test_web_simulator_routes_and_limits(client):
    response = post(client, '/workbench', {'tool': 'integer', 'value': 250, 'delta': 10, 'bits': 8})
    assert response.status_code == 200 and b'Unsigned Stored' in response.data
    assert post(client, '/workbench', {'tool': 'unknown'}).status_code == 400
    assert post(client, '/workbench', {'tool': 'integer', 'value': 'nan'}).status_code == 200
    assert client.post('/notebook', data={'body': 'x' * 140000}).status_code == 413


def test_all_pages_render_and_no_answer_key_leaked(client):
    for path in ('/', '/curriculum', '/practice', '/notebook', '/workbench'):
        assert client.get(path).status_code == 200
    for number in MODULES:
        assert client.get(f'/learn/{number}').status_code == 200
        assert client.get(f'/practice/{number}').status_code == 200
    html = client.get('/practice/42').data
    assert b'"answers"' not in html and b'data-correct' not in html


def test_entire_sequence_can_progress_with_valid_records(client, app):
    # Verifies curriculum plumbing, not the semantic quality of a learner's prose.
    for number in ORDER:
        data = prepare(client, app, number)
        response = post(client, f'/checkpoint/{number}/submit', data)
        assert response.status_code == 303, number
        with app.app_context():
            assert get_db().execute('SELECT passed FROM attempts ORDER BY id DESC LIMIT 1').fetchone()[0] == 1, number
    assert b'42 foundations' in client.get('/').data


def test_guided_lesson_order_and_distinct_worked_examples(client):
    for number, module in MODULES.items():
        html = client.get(f'/learn/{number}').get_data(as_text=True)
        markers = [f'id="{stage}"' for stage in ('purpose', 'explanation', 'resources', 'understanding')]
        assert [html.index(marker) for marker in markers] == sorted(html.index(marker) for marker in markers)
        assert module['teaching']['example'] != module['artifact']
        assert len(module['teaching']['steps']) >= 3
        assert len(module['understanding']) == 2
        assert module['teaching']['failure'] and module['teaching']['repair']


def test_assumptions_and_practice_cannot_be_skipped(client, app):
    data = submission(MODULES[42], app.secret_key)
    post(client, '/learn/42/read')
    assert post(client, '/practice/42/submit', data).status_code == 403
    assert client.get('/checkpoint/42').status_code == 403
    response = post(client, '/learn/42/check', {'prediction': 'wrong', 'principle': 'wrong'})
    assert response.status_code == 303
    assert b'An assumption needs another look' in client.get(response.location).data
    assert post(client, '/practice/42/submit', data).status_code == 403
    module = MODULES[42]
    quiz = {**module, 'id': f"understanding:42:{module['teaching']['version']}", 'probes': module['understanding']}
    post(client, '/learn/42/check', {p['key']: expected_choice(quiz, app.secret_key, p['key']) for p in quiz['probes']})
    assert post(client, '/checkpoint/42/submit', data).status_code == 403
    assert post(client, '/practice/42/submit', {**data, 'answer': 'A'}).status_code == 303
    assert client.get('/checkpoint/42').status_code == 403
    assert post(client, '/practice/42/submit', data).status_code == 303
    assert client.get('/checkpoint/42').status_code == 200
    assert b'Build the prerequisite model' in client.get('/practice/1').data
    with app.app_context():
        assert get_db().execute('SELECT count(*) FROM attempts').fetchone()[0] == 0


def test_final_checkpoint_requires_workflow_and_preserves_practice_evidence(client, app):
    data = prepare(client, app)
    response = post(client, '/checkpoint/42/submit', {**data, 'workflow': ''})
    assert b'Develop these entries' in client.get(response.location).data
    assert b'Build the prerequisite model' in client.get('/practice/1').data
    response = post(client, '/checkpoint/42/submit', {**data, 'answer': 'A', 'reasoning': 'tampered'})
    assert b'Your model holds' in client.get(response.location).data
    with app.app_context():
        payload = json.loads(get_db().execute('SELECT payload FROM attempts ORDER BY id DESC LIMIT 1').fetchone()[0])
        assert payload['answer'] == 'b' and payload['reasoning'] == RECORD['reasoning']
        assert payload['practice_run_id'] and payload['teaching_version']


def test_checkpoint_draft_survives_reload_and_exports_new_records(client, app):
    data = prepare(client, app)
    response = post(client, '/checkpoint/42/draft', {'workflow': RECORD['workflow'], 'reflection': RECORD['reflection']})
    assert response.location.endswith('/checkpoint/42')
    assert RECORD['workflow'].encode() in client.get(response.location).data
    assert RECORD['reasoning'].encode() in client.get('/practice/42').data
    bundle = client.get('/export').json
    assert len(bundle['understanding']) == 1 and len(bundle['practice_runs']) == 1


def test_preexisting_pass_is_not_invalidated_by_teaching_upgrade(client, app):
    with app.app_context(), get_db() as db:
        db.execute('INSERT INTO attempts(module_id,version,payload,result,notebook_snapshot,passed) VALUES (?,?,?,?,?,1)',
                   (42, MODULES[42]['version'], '{}', '{"passed":true,"checks":[]}', '{}'))
    assert b'Build the prerequisite model' not in client.get('/practice/1').data
    assert client.get('/attempts/1').status_code == 200
    assert client.get('/checkpoint/42').status_code == 403


def test_practice_revision_keeps_the_learners_final_draft(client, app):
    data = prepare(client, app)
    post(client, '/checkpoint/42/draft', {'workflow': RECORD['workflow'], 'reflection': RECORD['reflection']})
    post(client, '/practice/42/draft', {k: data[k] for k in ('answer', 'reasoning', 'hypothesis', 'observation')})
    post(client, '/practice/42/submit', data)
    assert RECORD['workflow'].encode() in client.get('/checkpoint/42').data
