import hmac
import json
import os
import secrets
import sqlite3
import threading
import time
from datetime import timedelta
from pathlib import Path

from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import SecurityError

from .curriculum import MODULES
from .db import SCHEMA, close_db, connect, get_db
from .grading import choices, evaluate, evaluate_practice, expected_choice
from .reviewer import ReviewUnavailable, review, validate_endpoint
from .simulations import integer_model, modbus_model, tank_model

REVIEW_LOCK = threading.Lock()
FIELDS = ('answer', 'hypothesis', 'reasoning', 'observation', 'reflection', 'code', 'model', 'evidence', 'transfer', 'confidence', 'note_id', 'reviewed', 'workflow')


def create_app(test_config=None):
    app = Flask(__name__)
    data_dir = Path(os.environ.get('LAB_DATA', './.lab-data'))
    app.config.update(
        DATABASE=str(data_dir / 'lab.sqlite3'), DATA_DIR=str(data_dir),
        MAX_CONTENT_LENGTH=128 * 1024, MAX_FORM_MEMORY_SIZE=128 * 1024,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict',
        SESSION_COOKIE_SECURE=os.environ.get('LAB_HTTPS') == '1',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        TRUSTED_HOSTS=os.environ.get('LAB_HOSTS', 'localhost,127.0.0.1').split(','),
        REVIEW_MODE=os.environ.get('LAB_REVIEW_MODE', 'structured'),
        REVIEW_URL=os.environ.get('LAB_REVIEW_URL', 'http://ollama:11434'),
        REVIEW_MODEL=os.environ.get('LAB_REVIEW_MODEL', 'qwen3:4b-instruct-2507-q4_K_M'),
    )
    if test_config:
        app.config.update(test_config)
    if app.config['REVIEW_MODE'] not in ('structured', 'local-ai'):
        raise ValueError('LAB_REVIEW_MODE must be structured or local-ai.')
    if app.config['REVIEW_MODE'] == 'local-ai':
        validate_endpoint(app.config['REVIEW_URL'])
    Path(app.config['DATA_DIR']).mkdir(mode=0o700, parents=True, exist_ok=True)
    db = connect(app.config['DATABASE'])
    db.executescript(SCHEMA)
    with db:
        for key in ('secret', 'setup_token'):
            db.execute('INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)', (key, secrets.token_urlsafe(32)))
    settings = dict(db.execute('SELECT key,value FROM settings').fetchall())
    app.config['SECRET_KEY'] = settings['secret']
    token_path = Path(app.config['DATA_DIR']) / 'setup-token'
    if not token_path.exists():
        try:
            with token_path.open('x') as file:
                file.write(settings['setup_token'] + '\n')
            token_path.chmod(0o600)
        except FileExistsError:
            pass
    db.close()
    app.teardown_appcontext(close_db)

    def completed():
        rows = get_db().execute('SELECT DISTINCT module_id,version FROM attempts WHERE passed=1').fetchall()
        return {row['module_id'] for row in rows if row['module_id'] in MODULES and row['version'] == MODULES[row['module_id']]['version']}

    def unlocked(module):
        return all(n in completed() for n in module['prerequisites'])

    def module_or_404(number):
        if number not in MODULES:
            abort(404)
        return MODULES[number]

    @app.before_request
    def protect():
        if isinstance(request.routing_exception, SecurityError):
            return 'Untrusted host.', 400
        if request.endpoint == 'static':
            return None
        g.account = get_db().execute('SELECT id FROM account WHERE id=1').fetchone()
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        if request.method == 'POST':
            supplied = request.form.get('csrf', '')
            if not supplied or not hmac.compare_digest(supplied, session['csrf']):
                abort(403, 'Form expired or invalid. Reload the page and try again.')
            origin = request.headers.get('Origin')
            if origin and origin != request.host_url.rstrip('/'):
                abort(403, 'Cross-origin submission rejected.')
        public = ('login', 'setup', 'health', 'static')
        if request.endpoint not in public:
            if not g.account:
                return redirect(url_for('setup'))
            if session.get('user') != 1:
                return redirect(url_for('login'))

    @app.after_request
    def security_headers(response):
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        # Keep same-origin form POSTs from receiving an opaque "null" Origin.
        # External links still receive no referrer.
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.context_processor
    def globals_for_templates():
        return {'curriculum': MODULES, 'csrf': session.get('csrf', ''), 'review_mode': app.config['REVIEW_MODE'], 'user': session.get('user')}

    def rate_limited():
        row = get_db().execute('SELECT * FROM login_failures WHERE address=?', (request.remote_addr,)).fetchone()
        return bool(row and time.time() - row['started'] < 900 and row['count'] >= 8)

    def fail_login():
        db = get_db()
        now = time.time()
        with db:
            db.execute('DELETE FROM login_failures WHERE started < ?', (now - 900,))
            db.execute('INSERT INTO login_failures(address,count,started) VALUES (?,1,?) ON CONFLICT(address) DO UPDATE SET count=count+1', (request.remote_addr, now))

    @app.route('/setup', methods=['GET', 'POST'])
    def setup():
        if g.account:
            return redirect(url_for('login'))
        if request.method == 'POST':
            if rate_limited():
                abort(429, 'Too many attempts. Wait 15 minutes.')
            stored = get_db().execute("SELECT value FROM settings WHERE key='setup_token'").fetchone()[0]
            if not hmac.compare_digest(request.form.get('token', ''), stored):
                fail_login()
                flash('The setup token is incorrect.', 'error')
            elif len(request.form.get('password', '')) < 12 or len(request.form.get('password', '')) > 256:
                flash('Use a password of 12–256 characters.', 'error')
            elif request.form.get('password') != request.form.get('confirm'):
                flash('Passwords do not match.', 'error')
            else:
                try:
                    with get_db() as db:
                        db.execute('INSERT INTO account(id,password_hash) VALUES (1,?)', (generate_password_hash(request.form['password']),))
                        db.execute("UPDATE settings SET value=? WHERE key='setup_token'", (secrets.token_urlsafe(32),))
                    session.clear()
                    flash('Your private account is ready. Sign in to begin.', 'success')
                    return redirect(url_for('login'), 303)
                except sqlite3.IntegrityError:
                    abort(409, 'Account setup has already completed.')
        return render_template('auth.html', setup=True)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if not g.account:
            return redirect(url_for('setup'))
        if request.method == 'POST':
            if rate_limited():
                abort(429, 'Too many attempts. Wait 15 minutes.')
            row = get_db().execute('SELECT password_hash FROM account WHERE id=1').fetchone()
            password = request.form.get('password', '')
            if len(password) <= 256 and check_password_hash(row['password_hash'], password):
                with get_db() as db:
                    db.execute('DELETE FROM login_failures WHERE address=?', (request.remote_addr,))
                session.clear()
                session['user'] = 1
                session['csrf'] = secrets.token_urlsafe(32)
                session.permanent = True
                return redirect(url_for('dashboard'), 303)
            fail_login()
            flash('Incorrect password.', 'error')
        return render_template('auth.html', setup=False)

    @app.post('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'), 303)

    @app.get('/health')
    def health():
        get_db().execute('SELECT 1')
        return jsonify(status='ok')

    @app.get('/')
    def dashboard():
        done = completed()
        current = next((m for m in MODULES.values() if m['id'] not in done), None)
        recent = get_db().execute('SELECT * FROM attempts ORDER BY id DESC LIMIT 5').fetchall()
        note_count = get_db().execute('SELECT count(*) FROM notes').fetchone()[0]
        return render_template('dashboard.html', done=done, current=current, recent=recent, note_count=note_count)

    @app.get('/curriculum')
    def curriculum():
        done = completed()
        return render_template('curriculum.html', done=done, available={m['id'] for m in MODULES.values() if unlocked(m)})

    @app.get('/practice')
    def practice_hub():
        return render_template('curriculum.html', practice_hub=True, done=completed(),
                               available={m['id'] for m in MODULES.values() if unlocked(m)})

    def lesson_read(module):
        return get_db().execute('SELECT 1 FROM reading WHERE module_id=? AND version=?',
                               (module['id'], module['teaching']['version'])).fetchone() is not None

    def understanding_record(module):
        row = get_db().execute('SELECT * FROM understanding WHERE module_id=? AND version=?',
                               (module['id'], module['teaching']['version'])).fetchone()
        return dict(row) if row else None

    def understanding_module(module):
        return {**module, 'id': f"understanding:{module['id']}:{module['teaching']['version']}", 'probes': module['understanding']}

    def require_learning(module):
        record = understanding_record(module)
        if not unlocked(module) or not lesson_read(module) or not record or not record['passed']:
            abort(403, 'Complete the prerequisite, lesson, and assumption checks before practice.')

    def latest_practice(module):
        return get_db().execute('SELECT * FROM practice_runs WHERE module_id=? AND version=? ORDER BY id DESC LIMIT 1',
                                (module['id'], module['teaching']['version'])).fetchone()

    @app.get('/learn/<int:number>')
    def learn(number):
        module = module_or_404(number)
        read = lesson_read(module)
        topics = {r['topic']: dict(r) for r in get_db().execute('SELECT * FROM topic_notes WHERE module_id=?', (number,)).fetchall()}
        record = understanding_record(module)
        return render_template('learn.html', module=module, read=read, unlocked=unlocked(module), topic_notes=topics,
                               understanding=record, understanding_result=json.loads(record['result']) if record else None,
                               understanding_payload=json.loads(record['payload']) if record else {},
                               learning_probes=choices(understanding_module(module), app.secret_key))

    @app.post('/learn/<int:number>/read')
    def mark_read(number):
        module = module_or_404(number)
        with get_db() as db:
            db.execute('INSERT INTO reading(module_id,version) VALUES (?,?) ON CONFLICT(module_id) DO UPDATE SET version=excluded.version, read_at=CURRENT_TIMESTAMP', (number, module['teaching']['version']))
        flash('Lesson recorded. Check your assumptions before opening practice.', 'success')
        return redirect(url_for('learn', number=number) + '#understanding', 303)

    @app.post('/learn/<int:number>/check')
    def check_understanding(number):
        module = module_or_404(number)
        if not unlocked(module) or not lesson_read(module):
            abort(403, 'Complete the prerequisite and record the lesson first.')
        quiz = understanding_module(module)
        payload = {p['key']: request.form.get(p['key'], '')[:200] for p in quiz['probes']}
        checks = []
        for probe in quiz['probes']:
            passed = payload[probe['key']] == expected_choice(quiz, app.secret_key, probe['key'])
            explanation = (' '.join(module['teaching']['steps']) + ' ' + module['teaching']['failure'] if probe['key'] == 'prediction' else module['teaching']['mechanism'])
            checks.append(dict(key=probe['key'], title=probe['title'], passed=passed,
                               feedback=explanation, correct_claim=probe['options'][0]))
        passed = all(c['passed'] for c in checks)
        result = dict(passed=passed, checks=checks)
        with get_db() as db:
            db.execute('INSERT INTO understanding(module_id,version,payload,result,passed) VALUES (?,?,?,?,?) '
                       'ON CONFLICT(module_id,version) DO UPDATE SET payload=excluded.payload,result=excluded.result,passed=excluded.passed,updated_at=CURRENT_TIMESTAMP',
                       (number, module['teaching']['version'], json.dumps(payload), json.dumps(result), int(passed)))
        return redirect(url_for('learn', number=number) + '#understanding', 303)

    @app.post('/learn/<int:number>/topic')
    def topic_note(number):
        module = module_or_404(number)
        topic = request.form.get('topic', '')
        if topic not in module['topics']:
            abort(400, 'Unknown topic.')
        explanation = request.form.get('explanation', '').strip()
        evidence = request.form.get('evidence', '').strip()
        if not 10 <= len(explanation) <= 5000 or not 5 <= len(evidence) <= 5000:
            abort(400, 'Provide a topic explanation (10–5000 characters) and evidence or source (5–5000 characters).')
        with get_db() as db:
            db.execute('INSERT INTO topic_notes(module_id,topic,explanation,evidence) VALUES (?,?,?,?) ON CONFLICT(module_id,topic) DO UPDATE SET explanation=excluded.explanation,evidence=excluded.evidence,updated_at=CURRENT_TIMESTAMP', (number, topic, explanation, evidence))
        flash('Topic research saved. This is a study record, not a mastery grade.', 'success')
        return redirect(url_for('learn', number=number) + '#topic-map', 303)

    @app.get('/practice/<int:number>')
    def practice(number):
        module = module_or_404(number)
        ready = unlocked(module)
        read = lesson_read(module)
        row = get_db().execute('SELECT payload FROM drafts WHERE module_id=?', (number,)).fetchone()
        draft = json.loads(row['payload']) if row else {}
        notes = get_db().execute('SELECT * FROM notes WHERE module_id=? ORDER BY id DESC', (number,)).fetchall()
        attempts = get_db().execute('SELECT * FROM attempts WHERE module_id=? ORDER BY id DESC', (number,)).fetchall()
        return render_template('practice.html', module=module, unlocked=ready, read=read,
                               probes=choices(module, app.secret_key) if ready else [], draft=draft, notes=notes, attempts=attempts,
                               understanding=understanding_record(module), practice_run=latest_practice(module))

    def submission_data():
        data = {key: request.form.get(key, '').strip() for key in FIELDS}
        if any(len(v) > 6000 for v in data.values()):
            abort(400, 'Each response is limited to 6,000 characters.')
        try:
            confidence = int(data['confidence'] or 50)
        except ValueError:
            abort(400, 'Confidence must be a number.')
        if confidence < 0 or confidence > 100:
            abort(400, 'Confidence must be between 0 and 100.')
        data['confidence'] = str(confidence)
        return data

    def merge_practice_draft(number, data):
        row = get_db().execute('SELECT payload FROM drafts WHERE module_id=?', (number,)).fetchone()
        previous = json.loads(row['payload']) if row else {}
        return {**previous, **{key: data[key] for key in ('answer', 'hypothesis', 'reasoning', 'observation', 'code', 'confidence')}}

    @app.post('/practice/<int:number>/draft')
    def save_draft(number):
        module = module_or_404(number)
        if not unlocked(module):
            abort(403, 'Complete the prerequisite checkpoint first.')
        data = merge_practice_draft(number, submission_data())
        with get_db() as db:
            db.execute('INSERT INTO drafts(module_id,payload) VALUES (?,?) ON CONFLICT(module_id) DO UPDATE SET payload=excluded.payload,updated_at=CURRENT_TIMESTAMP', (number, json.dumps(data)))
        flash('Draft saved locally.', 'success')
        return redirect(url_for('practice', number=number), 303)

    @app.post('/practice/<int:number>/submit')
    def practice_submit(number):
        module = module_or_404(number)
        require_learning(module)
        data = submission_data()
        result = evaluate_practice(module, data)
        draft = merge_practice_draft(number, data)
        with get_db() as db:
            db.execute('INSERT INTO practice_runs(module_id,version,payload,result,passed) VALUES (?,?,?,?,?)',
                       (number, module['teaching']['version'], json.dumps(data), json.dumps(result), int(result['passed'])))
            db.execute('INSERT INTO drafts(module_id,payload) VALUES (?,?) ON CONFLICT(module_id) DO UPDATE SET payload=excluded.payload,updated_at=CURRENT_TIMESTAMP',
                       (number, json.dumps(draft)))
        flash(result['feedback'], 'success' if result['passed'] else 'error')
        return redirect(url_for('checkpoint' if result['passed'] else 'practice', number=number), 303)

    @app.get('/checkpoint/<int:number>')
    def checkpoint(number):
        module = module_or_404(number)
        require_learning(module)
        run = latest_practice(module)
        if not run or not run['passed']:
            abort(403, 'Complete the practice problem before the final checkpoint.')
        row = get_db().execute('SELECT payload FROM drafts WHERE module_id=?', (number,)).fetchone()
        draft = json.loads(row['payload']) if row else {}
        notes = get_db().execute('SELECT * FROM notes WHERE module_id=? ORDER BY id DESC', (number,)).fetchall()
        return render_template('checkpoint.html', module=module, draft=draft, notes=notes,
                               practice_payload=json.loads(run['payload']), probes=choices(module, app.secret_key))

    @app.post('/checkpoint/<int:number>/draft')
    def checkpoint_draft(number):
        module = module_or_404(number)
        require_learning(module)
        run = latest_practice(module)
        if not run or not run['passed']:
            abort(403, 'Complete the practice problem first.')
        data = submission_data()
        practice_payload = json.loads(run['payload'])
        for key in ('answer', 'hypothesis', 'reasoning', 'observation', 'code', 'confidence'):
            data[key] = practice_payload.get(key, '')
        with get_db() as db:
            db.execute('INSERT INTO drafts(module_id,payload) VALUES (?,?) ON CONFLICT(module_id) DO UPDATE SET payload=excluded.payload,updated_at=CURRENT_TIMESTAMP',
                       (number, json.dumps(data)))
        flash('Final explanation draft saved.', 'success')
        return redirect(url_for('checkpoint', number=number), 303)

    @app.post('/checkpoint/<int:number>/submit')
    def submit(number):
        module = module_or_404(number)
        if not unlocked(module):
            abort(403, 'Complete the prerequisite checkpoint first.')
        require_learning(module)
        run = latest_practice(module)
        if not run or not run['passed']:
            abort(403, 'Complete the practice problem before the final checkpoint.')
        data = submission_data()
        # Practice evidence is server-owned: final forms cannot replace it with another result.
        practice_payload = json.loads(run['payload'])
        for key in ('answer', 'hypothesis', 'reasoning', 'observation', 'code', 'confidence'):
            data[key] = practice_payload.get(key, '')
        data['practice_run_id'] = run['id']
        data['teaching_version'] = module['teaching']['version']
        note = get_db().execute('SELECT * FROM notes WHERE id=? AND module_id=?', (data['note_id'], number)).fetchone()
        snapshot = dict(note) if note else {}
        result = evaluate(module, data, app.secret_key, snapshot)
        result['mode'] = app.config['REVIEW_MODE']
        # Store the draft before a potentially slow reviewer call; no open DB transaction during inference.
        with get_db() as db:
            db.execute('INSERT INTO drafts(module_id,payload) VALUES (?,?) ON CONFLICT(module_id) DO UPDATE SET payload=excluded.payload,updated_at=CURRENT_TIMESTAMP', (number, json.dumps(data)))
        if app.config['REVIEW_MODE'] == 'local-ai':
            if result['passed']:
                acquired = REVIEW_LOCK.acquire(blocking=False)
                try:
                    if not acquired:
                        raise ReviewUnavailable('A local review is already running. Your draft is saved; retry shortly.')
                    semantic = review(module, data, snapshot, app.config['REVIEW_URL'], app.config['REVIEW_MODEL'])
                    result['semantic'] = semantic
                    result['passed'] = semantic['passed']
                    result['state'] = 'checkpoint_passed' if semantic['passed'] else 'revise_model'
                    result['summary'] = 'Structured checks and local written review passed.' if semantic['passed'] else 'The local reviewer needs stronger or more consistent written reasoning.'
                    if semantic['verdict'] == 'uncertain':
                        result.update(passed=False, state='review_pending', summary='The local reviewer is uncertain about this record. Your draft is saved; inspect the feedback and retry. Uncertainty is not a finding that your explanation is wrong.')
                except ReviewUnavailable as error:
                    result.update(passed=False, state='review_pending', summary=str(error))
                finally:
                    if acquired:
                        REVIEW_LOCK.release()
            else:
                result['semantic_skipped'] = 'Complete the structured checks and research record before local written review.'
            result['assessment_scope'] = 'Structured checks plus a local AI review of your explanation, observations, reflection, complete workflow, and linked notebook. AI feedback is fallible; inspect its evidence quotes. This is a foundation checkpoint, not certification.'
        with get_db() as db:
            cursor = db.execute('INSERT INTO attempts(module_id,version,payload,result,notebook_snapshot,passed) VALUES (?,?,?,?,?,?)',
                                (number, module['version'], json.dumps(data), json.dumps(result), json.dumps(snapshot), int(result['passed'])))
            attempt_id = cursor.lastrowid
        return redirect(url_for('attempt', attempt_id=attempt_id), 303)

    @app.get('/attempts/<int:attempt_id>')
    def attempt(attempt_id):
        row = get_db().execute('SELECT * FROM attempts WHERE id=?', (attempt_id,)).fetchone()
        if not row:
            abort(404)
        module = module_or_404(row['module_id'])
        return render_template('attempt.html', attempt=row, module=module, result=json.loads(row['result']),
                               payload=json.loads(row['payload']), snapshot=json.loads(row['notebook_snapshot']))

    @app.route('/notebook', methods=['GET', 'POST'])
    def notebook():
        db = get_db()
        if request.method == 'POST':
            try:
                number = int(request.form.get('module_id', ''))
            except ValueError:
                abort(400, 'Choose a module.')
            module_or_404(number)
            kind, title, body = (request.form.get(key, '').strip() for key in ('kind', 'title', 'body'))
            if kind not in ('note', 'journal', 'observation') or not 1 <= len(title) <= 120 or not 1 <= len(body) <= 12000:
                abort(400, 'Choose a valid entry type, a title (up to 120 characters), and text (up to 12,000 characters).')
            note_id = request.form.get('id')
            with db:
                if note_id:
                    cursor = db.execute('UPDATE notes SET module_id=?,kind=?,title=?,body=?,updated_at=CURRENT_TIMESTAMP WHERE id=?', (number, kind, title, body, note_id))
                    if not cursor.rowcount:
                        abort(404)
                else:
                    db.execute('INSERT INTO notes(module_id,kind,title,body) VALUES (?,?,?,?)', (number, kind, title, body))
            flash('Notebook entry saved. Submitted attempts retain their original snapshot.', 'success')
            return redirect(url_for('notebook', module=number), 303)
        query = request.args.get('q', '')[:120]
        selected = request.args.get('module', type=int)
        if selected is not None:
            module_or_404(selected)
        edit_id = request.args.get('edit', type=int)
        editing = db.execute('SELECT * FROM notes WHERE id=?', (edit_id,)).fetchone() if edit_id else None
        entries = db.execute('SELECT * FROM notes WHERE (title LIKE ? OR body LIKE ?) AND (? IS NULL OR module_id=?) ORDER BY updated_at DESC,id DESC',
                             (f'%{query}%', f'%{query}%', selected, selected)).fetchall()
        return render_template('notebook.html', entries=entries, selected=selected, query=query, editing=editing)

    @app.get('/export')
    def export():
        tables = ('reading', 'notes', 'attempts', 'drafts', 'topic_notes', 'understanding', 'practice_runs')
        bundle = {'format': 'private-lab-export-v1', 'exported_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                  'curriculum_version': '2026.09.foundation.1'}
        for table in tables:
            bundle[table] = [dict(row) for row in get_db().execute(f'SELECT * FROM {table}').fetchall()]
        response = jsonify(bundle)
        response.headers['Content-Disposition'] = 'attachment; filename=research-lab-export.json'
        return response

    @app.route('/workbench', methods=['GET', 'POST'])
    def workbench():
        result = None
        tool = request.form.get('tool', 'integer')
        if request.method == 'POST':
            try:
                if tool == 'integer':
                    result = integer_model(*(int(request.form[k]) for k in ('value', 'delta', 'bits')))
                elif tool == 'tank':
                    result = tank_model(*(int(request.form[k]) for k in ('level', 'inflow', 'outflow', 'steps', 'trip')))
                elif tool == 'modbus':
                    result = modbus_model(request.form.get('frame', ''))
                else:
                    abort(400, 'Unknown simulator.')
            except (ValueError, KeyError) as error:
                flash(str(error), 'error')
        return render_template('workbench.html', result=result, tool=tool)

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(409)
    @app.errorhandler(413)
    @app.errorhandler(429)
    def error_page(error):
        return render_template('error.html', error=error), error.code

    return app
