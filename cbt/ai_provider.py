import hashlib
import json
import logging
import os
import re
import time
from typing import Any, Dict, List

from django.core.cache import cache
from openai import OpenAI

from .gemini_service import (
    GeminiAPIError,
    GeminiInvalidAPIKeyError,
    GeminiJSONError,
    GeminiModelNotFoundError,
    GeminiQuotaError,
    GeminiTimeoutError,
    _build_prompt,
    _make_gemini_request,
    validate_generated_question_payload,
)

logger = logging.getLogger(__name__)

GROQ_TIMEOUT = int(os.getenv('GROQ_TIMEOUT', '25'))
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
GROQ_CACHE_SECONDS = int(os.getenv('AI_GENERATION_CACHE_SECONDS', '120'))
GROQ_FAILURE_THRESHOLD = int(os.getenv('AI_GENERATION_FAILURE_THRESHOLD', '2'))
GROQ_FAILURE_WINDOW_SECONDS = int(os.getenv('AI_GENERATION_FAILURE_WINDOW_SECONDS', '60'))
GROQ_COOLDOWN_SECONDS = int(os.getenv('AI_GENERATION_COOLDOWN_SECONDS', '120'))
GROQ_LOCK_SECONDS = int(os.getenv('AI_GENERATION_LOCK_SECONDS', '30'))
AI_USE_GROQ = os.getenv('AI_USE_GROQ', 'true').strip().lower() not in ('0', 'false', 'no')

GROQ_FAILURE_KEY = 'cbt:ai:groq:failures'
GROQ_COOLDOWN_KEY = 'cbt:ai:groq:cooldown'


def _sanitize_text(text: Any) -> str:
    if not isinstance(text, str):
        return ''
    cleaned = text.strip()
    return re.sub(r'```(?:json)?\s*', '', cleaned, flags=re.IGNORECASE).strip()


def _strip_markdown_wrappers(text: str) -> str:
    cleaned = _sanitize_text(text)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    return cleaned


def _extract_first_json_candidate(text: str):
    cleaned = _strip_markdown_wrappers(text)
    if not cleaned:
        raise ValueError('Empty AI response received.')

    start_positions = [index for index, char in enumerate(cleaned) if char in '[{']
    decoder = json.JSONDecoder()

    for start in start_positions:
        try:
            parsed, _ = decoder.raw_decode(cleaned[start:])
            return parsed
        except json.JSONDecodeError:
            continue

    raise ValueError('No valid JSON object or array found in AI response.')


def _get_groq_client():
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise EnvironmentError('GROQ_API_KEY is not configured in environment.')

    return OpenAI(
        api_key=api_key,
        base_url='https://api.groq.com/openai/v1',
    )


def _groq_cache_key(prompt: str) -> str:
    digest = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
    return f'cbt:ai:groq:preview:{digest}'


def _groq_lock_key(prompt: str) -> str:
    digest = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
    return f'cbt:ai:groq:lock:{digest}'


def _groq_is_disabled() -> bool:
    until = cache.get(GROQ_COOLDOWN_KEY)
    if until is None:
        return False
    if float(until) > time.time():
        return True
    cache.delete(GROQ_COOLDOWN_KEY)
    return False


def _should_use_groq() -> bool:
    return AI_USE_GROQ


def _record_groq_failure() -> None:
    current = cache.get(GROQ_FAILURE_KEY) or 0
    current += 1
    cache.set(GROQ_FAILURE_KEY, current, GROQ_FAILURE_WINDOW_SECONDS)

    if current >= GROQ_FAILURE_THRESHOLD:
        cache.set(GROQ_COOLDOWN_KEY, time.time() + GROQ_COOLDOWN_SECONDS, GROQ_COOLDOWN_SECONDS)
        logger.warning(
            '[AI] Groq health fallback enabled for %ss after %s failures.',
            GROQ_COOLDOWN_SECONDS,
            current,
        )


def _clear_groq_failures() -> None:
    cache.delete(GROQ_FAILURE_KEY)
    cache.delete(GROQ_COOLDOWN_KEY)


def _validate_question_payload(question: Any, index: int) -> None:
    valid, error = validate_generated_question_payload(question)
    if not valid:
        raise GeminiJSONError(f'Question at index {index} is invalid: {error}')

    question_type = question.get('question_type')
    choices = question.get('choices', [])

    if question_type != 'short_answer':
        if not isinstance(choices, list) or len(choices) != 4:
            raise GeminiJSONError(f'Question at index {index} must include exactly 4 choices.')

        for choice_index, choice in enumerate(choices):
            if not isinstance(choice, dict):
                raise GeminiJSONError(f'Choice at index {choice_index} for question {index} must be an object.')
            if not isinstance(choice.get('text'), str) or not choice.get('text', '').strip():
                raise GeminiJSONError(f'Choice at index {choice_index} for question {index} must contain non-empty text.')
            if not isinstance(choice.get('is_correct'), bool):
                raise GeminiJSONError(f'Choice at index {choice_index} for question {index} must include a boolean is_correct value.')

    prompt = question.get('prompt')
    explanation = question.get('explanation')
    if not isinstance(prompt, str) or not prompt.strip():
        raise GeminiJSONError(f'Question at index {index} is missing a non-empty prompt.')
    if not isinstance(explanation, str) or not explanation.strip():
        raise GeminiJSONError(f'Question at index {index} is missing a non-empty explanation.')


def _normalize_questions(raw_questions: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw_questions, list):
        raise GeminiJSONError('AI response JSON must be an array of questions.')

    normalized = []
    for index, question in enumerate(raw_questions):
        if not isinstance(question, dict):
            raise GeminiJSONError(f'Question at index {index} must be an object.')
        _validate_question_payload(question, index)
        normalized.append(question)

    return normalized


def _log_metadata(provider: str, duration: float, fallback: bool, requested_questions: int) -> None:
    logger.info(
        '[AI] provider=%s duration=%.2fs fallback=%s requested_questions=%s',
        provider,
        duration,
        fallback,
        requested_questions,
    )


def generate_with_groq(prompt):
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError('Prompt is required for Groq generation.')

    if _groq_is_disabled():
        logger.warning('[AI] Groq is temporarily disabled in cache health fallback; using Gemini instead.')
        raise RuntimeError('Groq is temporarily disabled due to repeated failures.')

    client = _get_groq_client()
    start = time.monotonic()

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7,
            max_tokens=1500,
            timeout=GROQ_TIMEOUT,
        )
        content = getattr(response.choices[0].message, 'content', None) if response.choices else None
        if not content:
            raise RuntimeError('No text returned from Groq API.')

        duration = time.monotonic() - start
        logger.info('Groq provider succeeded in %.2fs.', duration)
        return _strip_markdown_wrappers(content)
    except Exception:
        logger.warning('Groq provider failed after %.2fs.', time.monotonic() - start, exc_info=True)
        raise


def generate_with_gemini(prompt):
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError('Prompt is required for Gemini generation.')

    logger.info('Using Gemini provider for AI question generation.')
    return _strip_markdown_wrappers(_make_gemini_request(prompt))


def _parse_ai_questions(raw_text: str) -> List[Dict[str, Any]]:
    try:
        parsed = _extract_first_json_candidate(raw_text)
    except ValueError as err:
        raise GeminiJSONError(str(err)) from err

    return _normalize_questions(parsed)


def _generate_questions(prompt: str, requested_questions: int):
    groq_error = None
    start = time.monotonic()

    if not _should_use_groq():
        logger.info('[AI] Groq disabled or unavailable; using Gemini provider only.')
        raw_text = generate_with_gemini(prompt)
        questions = _parse_ai_questions(raw_text)
        _log_metadata('gemini', time.monotonic() - start, False, requested_questions)
        return questions

    try:
        raw_text = generate_with_groq(prompt)
        questions = _parse_ai_questions(raw_text)
        _clear_groq_failures()
        _log_metadata('groq', time.monotonic() - start, False, requested_questions)
        return questions
    except Exception as exc:
        groq_error = exc
        _record_groq_failure()
        logger.warning(
            '[AI] provider=groq fallback=True requested_questions=%s reason=%s',
            requested_questions,
            exc.__class__.__name__,
        )

    try:
        raw_text = generate_with_gemini(prompt)
        questions = _parse_ai_questions(raw_text)
        _log_metadata('gemini', time.monotonic() - start, True, requested_questions)
        return questions
    except Exception as gemini_exc:
        logger.error(
            '[AI] Both providers failed. groq_error=%s gemini_error=%s',
            groq_error,
            gemini_exc,
            exc_info=True,
        )

        if isinstance(gemini_exc, GeminiTimeoutError):
            raise GeminiTimeoutError(
                f'Groq request failed and Gemini fallback timed out: {groq_error}'
            ) from gemini_exc
        if isinstance(gemini_exc, GeminiQuotaError):
            raise GeminiQuotaError(
                f'Groq request failed and Gemini fallback exceeded quota: {groq_error}'
            ) from gemini_exc
        if isinstance(gemini_exc, GeminiInvalidAPIKeyError):
            raise GeminiInvalidAPIKeyError(
                f'Groq request failed and Gemini fallback is not configured: {groq_error}'
            ) from gemini_exc
        if isinstance(gemini_exc, GeminiModelNotFoundError):
            raise GeminiModelNotFoundError(
                f'Groq request failed and Gemini fallback model is unavailable: {groq_error}'
            ) from gemini_exc
        if isinstance(gemini_exc, GeminiAPIError):
            raise GeminiAPIError(
                f'Groq request failed and Gemini fallback failed: {groq_error}; {gemini_exc}'
            ) from gemini_exc
        if isinstance(gemini_exc, EnvironmentError):
            raise GeminiInvalidAPIKeyError(
                f'Groq request failed and Gemini fallback is not configured: {groq_error}'
            ) from gemini_exc

        raise RuntimeError(
            f'Both AI providers failed. Groq: {groq_error}; Gemini: {gemini_exc}'
        ) from gemini_exc


def generate_ai_questions(prompt=None, *, exam=None, topic='', difficulty='', num_questions=5):
    if prompt is None:
        if exam is None:
            raise ValueError('Either prompt or exam metadata must be provided.')
        prompt = _build_prompt(exam, topic, difficulty, num_questions)

    cache_key = _groq_cache_key(prompt)
    cached_questions = cache.get(cache_key)
    if cached_questions is not None:
        logger.info(
            '[AI] provider=cache duration=0.00s fallback=False requested_questions=%s',
            num_questions,
        )
        return cached_questions

    lock_key = _groq_lock_key(prompt)
    lock_acquired = cache.add(lock_key, True, GROQ_LOCK_SECONDS)
    if not lock_acquired:
        for _ in range(6):
            time.sleep(0.2)
            cached_questions = cache.get(cache_key)
            if cached_questions is not None:
                logger.info(
                    '[AI] provider=cache duration=0.00s fallback=False requested_questions=%s',
                    num_questions,
                )
                return cached_questions

    try:
        questions = _generate_questions(prompt, num_questions)
        cache.set(cache_key, questions, GROQ_CACHE_SECONDS)
        return questions
    finally:
        cache.delete(lock_key)
