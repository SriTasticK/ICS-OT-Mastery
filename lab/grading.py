"""Deterministic causal-model assessment, deliberately not a prose classifier."""
import hashlib
import random
import re

DIMENSIONS = ('model', 'evidence', 'transfer')

def normalized(value):
    return ' '.join(str(value).strip().casefold().split())


def choices(module, secret):
    """Opaque stable choice IDs; correctness is never serialized to the browser."""
    result = []
    for probe in module['probes']:
        options = []
        for index, label in enumerate(probe['options']):
            token = hashlib.sha256(f"{secret}:{module['id']}:{probe['key']}:{index}".encode()).hexdigest()[:24]
            options.append({'value': token, 'label': label})
        random.Random(f"{secret}:{module['id']}:{probe['key']}").shuffle(options)
        result.append({**probe, 'options': options})
    return result


def expected_choice(module, secret, key):
    return hashlib.sha256(f"{secret}:{module['id']}:{key}:0".encode()).hexdigest()[:24]


def writing_complete(text):
    # Completeness only. This is never called a semantic or correctness score.
    words = re.findall(r"\w+", text, re.UNICODE)
    return len(words) >= 12 and len(set(w.casefold() for w in words)) >= 8


def evaluate(module, submission, secret, notebook):
    """All dimensions must pass; a correct result cannot offset a misconception."""
    checks = []
    for probe in module['probes']:
        passed = submission.get(probe['key']) == expected_choice(module, secret, probe['key'])
        checks.append({
            'key': probe['key'], 'label': probe['title'], 'passed': passed,
            'feedback': ('Your selected claim matches the case model.' if passed else
                         f"Revisit this principle: {probe['options'][0]}"),
        })
    model_pass = all(check['passed'] for check in checks)
    normalize_answer = (lambda value: ' '.join(str(value).strip().split())) if module.get('answer_case_sensitive') else normalized
    outcome = normalize_answer(submission.get('answer', '')) in {normalize_answer(a) for a in module['answers']}
    checks.append({'key': 'outcome', 'label': 'Observed result', 'passed': outcome,
                   'feedback': 'The result matches the case.' if outcome else 'Recompute from the supplied artifact. Check bounds, units, and assumptions.'})
    written_fields = ('hypothesis', 'reasoning', 'observation', 'reflection', 'workflow')
    missing = [field for field in written_fields if not writing_complete(submission.get(field, ''))]
    checks.append({'key': 'writing', 'label': 'Research record', 'passed': not missing,
                   'feedback': ('Hypothesis, explanation, observation, and reflection recorded. This check verifies completeness; the assessment scope describes any additional written review.' if not missing else
                                'Develop these entries with at least 12 words and 8 distinct words each: ' + ', '.join(missing))})
    has_note = bool(notebook and writing_complete(notebook['body']))
    checks.append({'key': 'notebook', 'label': 'Linked notebook', 'passed': has_note,
                   'feedback': 'The selected notebook entry is linked to this attempt.' if has_note else 'Link a saved entry for this module with at least 12 words and 8 distinct words.'})
    checks.append({'key': 'review', 'label': 'Consistency review', 'passed': submission.get('reviewed') == 'yes',
                   'feedback': 'You attested that your prose agrees with your selected claims.' if submission.get('reviewed') == 'yes' else 'Review your written explanation against the causal claims before submitting.'})
    passed = all(check['passed'] for check in checks)
    confidence = int(submission.get('confidence', '50'))
    return {
        'passed': passed,
        'state': 'checkpoint_passed' if passed else 'revise_model' if not model_pass else 'revise_evidence',
        'checks': checks,
        'summary': ('Foundation checkpoint passed. The next module is available.' if passed else
                    'Your causal model needs revision before this checkpoint can pass.' if not model_pass else
                    'The structured model is consistent; complete the remaining result or research evidence.'),
        'calibration': ('High confidence and an incorrect model: revisit the assumption before retrying.' if confidence >= 80 and not model_pass else
                        'Confidence is recorded for reflection; it does not add or subtract marks.'),
        'assessment_scope': 'Deterministic result and structured reasoning checks. Written work is checked for completeness and self-reviewed, not understood by an AI. Passing is foundation-level evidence, not certification of the full subject.',
    }


def evaluate_practice(module, submission):
    normalize = (lambda value: ' '.join(str(value).strip().split())) if module.get('answer_case_sensitive') else normalized
    outcome = normalize(submission.get('answer', '')) in {normalize(a) for a in module['answers']}
    missing = [field for field in ('hypothesis', 'reasoning', 'observation') if not writing_complete(submission.get(field, ''))]
    return {'passed': outcome and not missing, 'outcome': outcome, 'missing': missing,
            'feedback': ('The case result matches. Now explain the complete workflow at the final checkpoint; this has not unlocked the next module.' if outcome and not missing else
                         'Recompute the result from the artifact and record your prediction, reasoning, and observations. Each written field needs at least 12 words and 8 distinct words.')}
