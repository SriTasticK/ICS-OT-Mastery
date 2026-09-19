"""Browser validation against an automatically created disposable localhost app."""
from pathlib import Path
import sys
import tempfile
import threading
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from lab.app import create_app
from lab.curriculum import MODULES

ARTIFACTS = Path('artifacts')
ARTIFACTS.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='guided-lab-browser-') as directory:
    app = create_app({'TESTING': True, 'DATA_DIR': directory, 'DATABASE': directory + '/lab.sqlite3', 'REVIEW_MODE': 'structured'})
    server = make_server('127.0.0.1', 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    root = f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--disable-gpu'])
            page = browser.new_page(viewport={'width': 1440, 'height': 1080})
            errors = []
            page.on('pageerror', lambda err: errors.append(str(err)))
            page.goto(root)
            page.get_by_label('Setup token').fill(Path(directory, 'setup-token').read_text().strip())
            page.get_by_label('Create a password', exact=True).fill('temporary browser test password')
            page.get_by_label('Confirm password').fill('temporary browser test password')
            page.get_by_role('button', name='Create workspace').click()
            page.get_by_label('Password', exact=True).fill('temporary browser test password')
            page.get_by_role('button', name='Sign in').click()
            page.get_by_role('heading', name='Build a model.').wait_for()
            page.goto(root + '/learn/42')
            page.screenshot(path=str(ARTIFACTS / 'guided-purpose-desktop.png'))
            page.get_by_text('Walk through the example', exact=True).click()
            assert page.get_by_text('List the original boundary:', exact=False).is_visible()
            page.locator('#explanation').scroll_into_view_if_needed()
            page.screenshot(path=str(ARTIFACTS / 'guided-explanation-desktop.png'))
            page.locator('form[action="/learn/42/read"] button').click()
            # An incorrect prediction provides explanatory feedback and keeps practice locked.
            page.get_by_label('Continue because the simulator was already approved', exact=True).check()
            page.get_by_label(MODULES[42]['teaching']['mental_model'], exact=True).check()
            page.get_by_role('button', name='Check my assumptions', exact=True).click()
            assert page.get_by_text('An assumption needs another look.', exact=False).is_visible()
            page.get_by_label('Stop and reassess permission and physical safeguards', exact=True).check()
            page.get_by_role('button', name='Check my assumptions', exact=True).click()
            page.get_by_role('link', name='Apply the model in practice').click()
            page.get_by_label('Initial hypothesis').fill('I expect lab B to stay within the permitted scope because it contains only synthetic assets and has no physical outputs.')
            page.get_by_label('Your answer to the case').fill('B')
            page.get_by_label('Why does this result follow?').fill('Authorization covers synthetic assets only and lab B satisfies this condition while lab A connects to a real pump controller.')
            page.get_by_label('Evidence and observations').fill('The artifact describes lab B as using an internal network with no physical input or output and a saved snapshot.')
            page.get_by_role('button', name='Save draft', exact=True).click()
            page.get_by_role('button', name='Check practice result').click()
            assert '/checkpoint/42' in page.url
            page.goto(root + '/practice/1')
            assert page.get_by_role('heading', name='Build the prerequisite model first.').is_visible()
            page.goto(root + '/notebook?module=42')
            page.get_by_label('Title', exact=True).fill('Synthetic boundaries and stop conditions')
            page.get_by_label('Research entry', exact=True).fill('The synthetic lab stays within the permitted scope because no physical actuator is attached. A virtual machine alone does not guarantee isolation or authorization.')
            page.get_by_role('button', name='Save entry').click()
            page.goto(root + '/checkpoint/42')
            page.get_by_label('Complete workflow in your own words').fill('Authorization sets the permitted assets and actions while isolation constrains possible effects. The artifact describes B as synthetic with no physical I/O, meeting the stated boundary. Connecting an actuator would break this assumption; I would prevent this by keeping real hardware disconnected and reassessing authorization before any change. A route to a real pump in A does not provide permission to interact with it.')
            for probe in MODULES[42]['probes']:
                page.get_by_label(probe['options'][0], exact=True).check()
            page.get_by_label('Revised mental model').fill('Connecting a physical actuator would invalidate my assumptions so I would stop and reassess permission and safety before continuing the experiment.')
            options = page.locator('#note_id option').all()
            page.get_by_label('Link a saved notebook').select_option(options[-1].get_attribute('value'))
            page.get_by_label('I compared my written explanation').check()
            page.get_by_role('button', name='Save draft', exact=True).click()
            assert '/checkpoint/42' in page.url
            page.screenshot(path=str(ARTIFACTS / 'guided-checkpoint-desktop.png'))
            page.get_by_role('button', name='Evaluate checkpoint').click()
            page.get_by_role('heading', name='Your model holds for this case.').wait_for()
            page.screenshot(path=str(ARTIFACTS / 'guided-review-desktop.png'), full_page=True)
            page.get_by_role('link', name='Next: Core computer science').click()
            assert '/learn/1' in page.url
            page.set_viewport_size({'width': 390, 'height': 844})
            for route in ('/', '/learn/42', '/practice/42', '/checkpoint/42', '/notebook'):
                page.goto(root + route)
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), route
            page.goto(root + '/learn/42')
            page.screenshot(path=str(ARTIFACTS / 'guided-purpose-mobile.png'))
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
print('Browser passed: guided explanation, corrective assumption checks, practice gate, separate teach-back, draft persistence, notebook, final unlock, and mobile layouts. Disposable database only.')
