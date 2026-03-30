from __future__ import annotations
import re, uuid, json, logging
from dataclasses import dataclass
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


def _cfg():
    try:
        from django.conf import settings
        return getattr(settings, 'GIGACHAT_CLIENT_ID', ''), getattr(settings, 'GIGACHAT_SECRET', '')
    except Exception:
        return '', ''


@dataclass
class CheckResult:
    grade: float | None
    feedback: str
    raw_response: str = ''


def _get_access_token(client_id, secret):
    try:
        res = requests.post(
            'https://ngw.devices.sberbank.ru:9443/api/v2/oauth',
            headers={'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json', 'RqUID': str(uuid.uuid4())},
            auth=HTTPBasicAuth(client_id, secret),
            data={'scope': 'GIGACHAT_API_PERS'},
            verify=False, timeout=10,
        )
        res.raise_for_status()
        return res.json().get('access_token')
    except Exception as exc:
        logger.error('GigaChat token error: %s', exc)
        return None


def _send_prompt(prompt, token):
    try:
        res = requests.post(
            'https://gigachat.devices.sberbank.ru/api/v1/chat/completions',
            headers={'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'Bearer {token}'},
            data=json.dumps({'model': 'GigaChat', 'temperature': 0, 'messages': [{'role': 'user', 'content': prompt}]}),
            verify=False, timeout=30,
        )
        res.raise_for_status()
        return res.json()['choices'][0]['message']['content']
    except Exception as exc:
        logger.error('GigaChat error: %s', exc)
        return ''


def _extract_grade(text):
    match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*10', text)
    return min(max(float(match.group(1)), 0.0), 10.0) if match else None


def check_answer(question, answer, question_type='text', language=None) -> CheckResult:
    client_id, secret = _cfg()
    if not client_id:
        return CheckResult(grade=None, feedback='AI grading not configured.')
    token = _get_access_token(client_id, secret)
    if not token:
        return CheckResult(grade=None, feedback='Could not authenticate with GigaChat.')

    if question_type == 'code':
        lang = language or 'code'
        prompt = f'You are a senior {lang} engineer. Task: {question}\n\nCode:\n```{lang}\n{answer}\n```\n\nGrade 0-10, give feedback. End with: GRADE: X/10'
    else:
        prompt = f'You are a grader. Question: {question}\n\nAnswer: {answer}\n\nGrade 0-10, explain. End with: GRADE: X/10'

    raw = _send_prompt(prompt, token)
    if not raw:
        return CheckResult(grade=None, feedback='No response from GigaChat.')
    return CheckResult(grade=_extract_grade(raw), feedback=raw, raw_response=raw)