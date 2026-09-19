import io
import json
import pytest
from lab.curriculum import MODULES
from lab.reviewer import ReviewUnavailable, review, evidence_segments

PAYLOAD = {
    'answer': 'b',
    'hypothesis': 'I initially predicted that the synthetic environment would respect the authorization boundary.',
    'reasoning': 'Authorization is limited to synthetic assets, and lab B has no physical connections.',
    'observation': 'The artifact explicitly says internal network, no physical I/O, and snapshot for lab B.',
    'reflection': 'Attaching a real actuator invalidates the original isolation and authorization assumptions.',
    'workflow': 'Isolation bounds effects and authorization bounds permitted actions. The artifact states B has synthetic assets without physical I/O, so it fits this scope. Attaching a real actuator breaks the assumption; prevent that by keeping physical I/O disconnected and reassessing permission before changes.',
    'code': '',
}
NOTE = {'title': 'Boundary evidence', 'body': 'A real actuator would violate the stated synthetic-only scope even when the network remains internal.'}


def fake_model(monkeypatch, mutate=None, done_reason='stop'):
    calls = []
    class Opener:
        def open(self, request, timeout):
            sent = json.loads(request.data)
            field_input = json.loads(sent['messages'][1]['content'])
            field = field_input['field']
            calls.append(field_input)
            assert list(sent['format']['properties']) == ['assessment', 'evidence_refs', 'score']
            assert sent['options']['num_ctx'] == 4096
            assert 0 < timeout <= 90
            # The model cannot borrow a correct answer from another learner field.
            assert all(key.startswith(field + ':') for key in field_input['CANDIDATE_TO_GRADE'])
            reference_checks = field_input['REFERENCE_NOT_LEARNER_TEXT']['reference_checks']
            assert reference_checks[2]['question'] == MODULES[42]['probes'][2]['question']
            result = {'assessment': 'This candidate makes a concrete claim consistent with the case reference.', 'evidence_refs': [field + ':1'], 'score': 2}
            if mutate:
                result = mutate(field, result)
            content = result if isinstance(result, str) else json.dumps(result)
            return io.BytesIO(json.dumps({'message': {'content': content}, 'done': True, 'done_reason': done_reason}).encode())
    monkeypatch.setattr('lab.reviewer.urllib.request.build_opener', lambda *args: Opener())
    return calls


def test_verified_independent_local_review(monkeypatch):
    calls = fake_model(monkeypatch)
    result = review(MODULES[42], PAYLOAD, NOTE, 'http://ollama:11434', 'qwen3:4b')
    assert result['passed'] and result['model'] == 'qwen3:4b'
    assert [c['field'] for c in calls] == ['reasoning', 'evidence', 'transfer', 'notebook', 'workflow']
    assert result['quotes']['transfer'] == PAYLOAD['reflection']
    assert result['quotes']['notebook'] == NOTE['body']
    assert result['rubric_version'] == 'independent-fields-v4-teachback'


@pytest.mark.parametrize('mutation', ['cross_field','unknown_id','bad_score','missing_assessment','invalid_json','missing_evidence','duplicate_evidence'])
def test_malformed_or_unverifiable_feedback_fails_closed(monkeypatch, mutation):
    def mutate(field, result):
        if mutation == 'cross_field': result['evidence_refs'] = ['notebook:1']
        elif mutation == 'unknown_id': result['evidence_refs'] = ['reasoning:99']
        elif mutation == 'bad_score': result['score'] = True
        elif mutation == 'missing_assessment': del result['assessment']
        elif mutation == 'invalid_json': return 'invalid JSON'
        elif mutation == 'missing_evidence': result['evidence_refs'] = []
        elif mutation == 'duplicate_evidence': result['evidence_refs'] *= 2
        return result
    fake_model(monkeypatch, mutate)
    with pytest.raises(ReviewUnavailable):
        review(MODULES[42], PAYLOAD, NOTE, 'http://ollama:11434', 'qwen3:4b')


@pytest.mark.parametrize('field', ['reasoning','evidence','transfer','notebook','workflow','code'])
def test_one_bad_field_cannot_be_offset_by_good_fields(monkeypatch, field):
    fake_model(monkeypatch, lambda key, result: {**result, 'score': 0 if key == field else 3})
    result = review(MODULES[42], {**PAYLOAD, 'code': 'A final code claim to assess.'}, NOTE, 'http://ollama:11434', 'qwen3:4b')
    assert not result['passed'] and result['verdict'] == 'revise'
    assert result[field] == 0


def test_uncertainty_does_not_award_pass(monkeypatch):
    fake_model(monkeypatch, lambda key, result: {**result, 'score': -1 if key == 'reasoning' else 2})
    result = review(MODULES[42], PAYLOAD, NOTE, 'http://ollama:11434', 'qwen3:4b')
    assert not result['passed'] and result['verdict'] == 'uncertain'


def test_input_not_silently_truncated():
    with pytest.raises(ReviewUnavailable, match='small GPU review budget'):
        review(MODULES[42], {**PAYLOAD, 'code': 'x' * 9000}, NOTE, 'http://ollama:11434', 'qwen3:4b')


def test_evidence_segments_preserve_exact_source_substrings():
    text = 'First observation.  Second observation!\nA third line without punctuation'
    segments = evidence_segments({'reasoning': text})['reasoning']
    assert list(segments) == ['reasoning:1', 'reasoning:2', 'reasoning:3']
    assert all(part in text for part in segments.values())


def test_low_score_can_explain_absent_evidence(monkeypatch):
    fake_model(monkeypatch, lambda key, result: {**result, 'score': 1, 'evidence_refs': []} if key == 'transfer' else result)
    result = review(MODULES[42], PAYLOAD, NOTE, 'http://ollama:11434', 'qwen3:4b')
    assert not result['passed'] and result['quotes']['transfer'] == ''


def test_truncated_response_does_not_award_pass(monkeypatch):
    fake_model(monkeypatch, done_reason='length')
    with pytest.raises(ReviewUnavailable):
        review(MODULES[42], PAYLOAD, NOTE, 'http://ollama:11434', 'qwen3:4b')
