import json
import logging
import os
import re
import time
from typing import Any, Dict, List

# Avoid importing Django models at module import time to prevent AppRegistryNotReady
CBTQuestion = None

logger = logging.getLogger(__name__)

GEMINI_TIMEOUT = int(os.getenv('GEMINI_TIMEOUT', '30'))
GEMINI_RETRIES = int(os.getenv('GEMINI_RETRIES', '3'))
DEFAULT_GEMINI_MODEL = 'gemini-2.0-flash'
GEMINI_MODEL_FALLBACKS = [
    'gemini-1.5-flash-latest',
    'gemini-1.5-pro-latest',
]

# Keep backward compatibility with existing environment variable configuration.
# If GEMINI_MODEL is set, use it. Otherwise default to the currently preferred model.
GEMINI_MODEL = os.getenv('GEMINI_MODEL', DEFAULT_GEMINI_MODEL)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MOCK_MODE = os.getenv('GEMINI_MOCK_MODE', 'false').strip().lower() in ('1', 'true', 'yes')


class GeminiAPIError(Exception):
    """Base exception for Gemini integration issues."""


class GeminiQuotaError(GeminiAPIError):
    """Gemini quota or rate-limit conditions."""


class GeminiInvalidAPIKeyError(GeminiAPIError):
    """Gemini authentication failures."""


class GeminiModelNotFoundError(GeminiAPIError):
    """Gemini model is not available for the current API version."""


class GeminiTimeoutError(GeminiAPIError):
    """Gemini service timeout or unavailable."""


class GeminiJSONError(GeminiAPIError):
    """Gemini returned invalid JSON or unparsable content."""

try:
    from google import genai
    from google.genai.types import GenerateContentConfig
    GEMINI_SDK_VERSION = getattr(genai, '__version__', 'unknown')
    logger.info(
        'Gemini SDK import successful. sdk_version=%s active_model=%s',
        GEMINI_SDK_VERSION,
        GEMINI_MODEL,
    )
except ImportError:  # pragma: no cover
    genai = None
    GenerateContentConfig = None
    GEMINI_SDK_VERSION = None
    logger.warning(
        'Gemini SDK package google-genai is unavailable. Gemini integration is disabled until the package is installed.'
    )


def is_gemini_mock_mode() -> bool:
    return GEMINI_MOCK_MODE


def get_gemini_model() -> str:
    """Return the configured Gemini model.

    Gemini model names change over time. Latest aliases are more stable,
    while hardcoding old model names can break deployments when models get
    retired or renamed.
    """
    model = os.getenv('GEMINI_MODEL', '').strip() or GEMINI_MODEL
    model = model or DEFAULT_GEMINI_MODEL
    logger.debug('Determined Gemini model name: %s', model)
    return model


def _is_model_not_found_error(exc: Exception) -> bool:
    message = str(exc)
    return (
        'NOT_FOUND' in message.upper() or
        'not found' in message.lower() or
        ('model' in message.lower() and 'not found' in message.lower())
    )


def _is_quota_error(exc: Exception) -> bool:
    message = str(exc)
    return (
        'RESOURCE_EXHAUSTED' in message.upper() or
        'quota exceeded' in message.lower() or
        'rate limit' in message.lower() or
        'rate-limit' in message.lower()
    )


def _is_invalid_api_key_error(exc: Exception) -> bool:
    message = str(exc)
    return (
        '401' in message or
        'invalid api key' in message.lower() or
        'authentication' in message.lower() and 'failed' in message.lower()
    )


def _is_timeout_error(exc: Exception) -> bool:
    message = str(exc)
    return (
        'timeout' in message.lower() or
        'timed out' in message.lower() or
        'deadlineexceeded' in message.lower() or
        'deadline exceeded' in message.lower() or
        'service unavailable' in message.lower()
    )


def _record_gemini_request_event(status: str, latency: float, model: str, error_code: str = None, tokens_used: int = None):
    logger.info(
        'Gemini request event: status=%s model=%s latency=%.3f tokens=%s error=%s',
        status,
        model,
        latency,
        tokens_used,
        error_code,
    )


def _format_gemini_error_message(exc: Exception) -> str:
    if _is_quota_error(exc):
        return (
            'AI question generation is temporarily unavailable because the Gemini API quota has been exceeded. '
            'Please try again later, check Gemini billing/quota, or reduce the number of generated questions.'
        )
    if _is_invalid_api_key_error(exc):
        return (
            'AI question generation is unavailable because the Gemini API key is invalid. '
            'Please verify the GEMINI_API_KEY configuration.'
        )
    if _is_model_not_found_error(exc):
        return (
            'AI question generation is unavailable because the configured Gemini model is invalid or unavailable. '
            'Please verify the model configuration.'
        )
    if _is_timeout_error(exc):
        return (
            'AI question generation is temporarily unavailable. Please try again in a few minutes.'
        )
    return str(exc)


def _translate_gemini_exception(exc: Exception) -> GeminiAPIError:
    if _is_quota_error(exc):
        return GeminiQuotaError(_format_gemini_error_message(exc))
    if _is_invalid_api_key_error(exc):
        return GeminiInvalidAPIKeyError(_format_gemini_error_message(exc))
    if _is_model_not_found_error(exc):
        return GeminiModelNotFoundError(_format_gemini_error_message(exc))
    if _is_timeout_error(exc):
        return GeminiTimeoutError(_format_gemini_error_message(exc))
        return GeminiAPIError(_format_gemini_error_message(exc))


def _build_prompt(exam, topic, difficulty, num_questions):
    subject_name = getattr(exam.subject, 'name', 'General Knowledge')
    exam_mode = exam.get_exam_mode_display() if hasattr(exam, 'get_exam_mode_display') else 'Exam'
    prompt += (
        "Respond ONLY with a valid JSON array.\n\n"

    "Each object MUST contain:\n"
    "- prompt\n"
    "- question_type\n"
    "- mark_value\n"
    "- topic\n"
    "- difficulty\n"
    "- explanation\n"
    "- choices\n\n"

    "question_type MUST be EXACTLY one of:\n"
    "- mcq\n"
    "- multiple\n"
    "- true_false\n"
    "- short_answer\n\n"

    "difficulty MUST be EXACTLY one of:\n"
    "- easy\n"
    "- medium\n"
    "- hard\n\n"

    "For mcq, multiple and true_false, include exactly 4 choices.\n"
    "Each choice must contain:\n"
    "- text\n"
    "- is_correct\n"
    "- order\n\n"

    "For short_answer, choices must be an empty array.\n"

    "Return ONLY JSON."
)
    if topic:
        prompt += f"Focus on the topic: {topic}. "

        prompt += (
            "Respond with a JSON array of objects where each object has the keys: prompt, question_type, mark_value, topic, difficulty, explanation, choices. "
            "For choice-based questions include a 'choices' array containing objects with keys text, is_correct, order. "
            "For short_answer questions, choices may be an empty array. "
            "Do not include any additional text outside valid JSON."
    )
    return prompt


def _parse_json_from_text(text):
    if not text:
        raise ValueError('Empty response from Gemini')

    cleaned = text.strip()
    cleaned = re.sub(r'```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)

    array_match = re.search(r'\[.*\]', cleaned, flags=re.DOTALL)
    object_match = re.search(r'\{.*\}', cleaned, flags=re.DOTALL)
    candidate = array_match.group(0) if array_match else object_match.group(0) if object_match else cleaned

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as err:
        raise ValueError(f'Unable to parse JSON from AI response: {err}')


def _generate_mock_response(num_questions: int, topic: str) -> str:
    sample_questions = []
    for idx in range(1, num_questions + 1):
        sample_questions.append({
            'prompt': f'Sample question {idx} about {topic or "general knowledge"}.',
            'question_type': 'mcq',
            'mark_value': 1.0,
            'topic': topic or 'General',
            'difficulty': 'medium',
            'explanation': f'This is a sample explanation for sample question {idx}.',
            'choices': [
                {'text': 'Option A', 'is_correct': idx % 4 == 1, 'order': 0},
                {'text': 'Option B', 'is_correct': idx % 4 == 2, 'order': 1},
                {'text': 'Option C', 'is_correct': idx % 4 == 3, 'order': 2},
                {'text': 'Option D', 'is_correct': idx % 4 == 0, 'order': 3},
            ],
        })
    return json.dumps(sample_questions)


def _extract_token_usage(response):
    if not response:
        return None
    if hasattr(response, 'token_usage'):
        usage = getattr(response, 'token_usage')
        return getattr(usage, 'total', None) or getattr(usage, 'total_tokens', None) or usage
    if hasattr(response, 'usage'):
        usage = getattr(response, 'usage')
        return getattr(usage, 'total_tokens', None) or getattr(usage, 'prompt_tokens', None) or usage
    return None


def _make_gemini_request(prompt):
    if genai is None or GenerateContentConfig is None:
        raise ImportError(
            'Gemini integration requires the google-genai package. '
            'Install google-genai and restart the app.'
        )
    if not GEMINI_API_KEY:
        raise EnvironmentError(
            'Gemini API key is not configured. Set GEMINI_API_KEY in environment.'
        )

    model_name = get_gemini_model()
    client = genai.Client(api_key=GEMINI_API_KEY)
    logger.info(
        'Gemini SDK initialization success. model=%s sdk_version=%s',
        model_name,
        GEMINI_SDK_VERSION,
    )

    config = GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        max_output_tokens=1200,
        candidate_count=1,
    )

    start_time = time.monotonic()
    used_model = model_name
    response = None
    try:
        response = client.models.generate_content(
            model=used_model,
            contents=prompt,
            config=config,
        )
    except Exception as exc:
        if _is_model_not_found_error(exc) and model_name != GEMINI_MODEL_FALLBACKS[0]:
            fallback_model = GEMINI_MODEL_FALLBACKS[0]
            logger.warning(
                'Gemini model %s not found. Retrying once with fallback model %s.',
                model_name,
                fallback_model,
            )
            used_model = fallback_model
            try:
                response = client.models.generate_content(
                    model=used_model,
                    contents=prompt,
                    config=config,
                )
            except Exception as exc2:
                latency = time.monotonic() - start_time
                _record_gemini_request_event(
                    status='failure',
                    latency=latency,
                    model=used_model,
                    error_code=exc2.__class__.__name__,
                    tokens_used=None,
                )
                raise _translate_gemini_exception(exc2)
        else:
            latency = time.monotonic() - start_time
            _record_gemini_request_event(
                status='failure',
                latency=latency,
                model=used_model,
                error_code=exc.__class__.__name__,
                tokens_used=None,
            )
            raise _translate_gemini_exception(exc)

    latency = time.monotonic() - start_time
    token_usage = _extract_token_usage(response)
    response_model = getattr(response, 'model', None)
    _record_gemini_request_event(
        status='success',
        latency=latency,
        model=response_model or used_model,
        error_code=None,
        tokens_used=token_usage,
    )

    logger.info('Gemini generate_content response model=%s', response_model or used_model)

    text = getattr(response, 'text', None)
    if not text:
        raise GeminiJSONError('No text returned from Gemini API')
    return text


def generate_mock_questions(num_questions: int, topic: str = '') -> List[Dict[str, Any]]:
    sample_questions = []
    for idx in range(1, num_questions + 1):
        sample_questions.append({
            'prompt': f'Sample question {idx} about {topic or "general knowledge"}.',
            'question_type': 'mcq',
            'mark_value': 1.0,
            'topic': topic or 'General',
            'difficulty': 'medium',
            'explanation': f'This is a sample explanation for sample question {idx}.',
            'choices': [
                {'text': 'Option A', 'is_correct': idx % 4 == 1, 'order': 0},
                {'text': 'Option B', 'is_correct': idx % 4 == 2, 'order': 1},
                {'text': 'Option C', 'is_correct': idx % 4 == 3, 'order': 2},
                {'text': 'Option D', 'is_correct': idx % 4 == 0, 'order': 3},
            ],
        })
    return sample_questions


def generate_ai_questions_using_gemini(exam, topic, difficulty, num_questions):
    if is_gemini_mock_mode():
        logger.warning('Gemini mock mode enabled; generating sample questions locally.')
        return generate_mock_questions(num_questions=num_questions, topic=topic)

    prompt = _build_prompt(exam, topic, difficulty, num_questions)
    response_text = _make_gemini_request(prompt)
    try:
        parsed = _parse_json_from_text(response_text)
    except ValueError as err:
        raise GeminiJSONError(str(err)) from err

    if not isinstance(parsed, list):
        raise GeminiJSONError('Gemini response JSON must be an array of questions.')
    return parsed


def _clean_response_text(text: str) -> str:
    """Remove markdown fences and wrappers so JSON parsing is stable.

    AI responses often include human-friendly formatting (```json blocks,
    explanatory text). We strip those wrappers to improve json.loads()
    reliability.
    """
    if not isinstance(text, str):
        return ''
    cleaned = re.sub(r'```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    # Trim any leading non-json characters before the first { or [
    m = re.search(r'([\[\{])', cleaned)
    if m:
        cleaned = cleaned[m.start():]
    return cleaned.strip()


def _validate_strict_questions(parsed: Any) -> List[Dict[str, Any]]:
    if not isinstance(parsed, list):
        raise ValueError('Response must be a JSON array')
    normalized: List[Dict[str, Any]] = []
    for idx, item in enumerate(parsed):
        if not isinstance(item, dict):
            raise ValueError(f'Question at index {idx} must be an object')
        q = item.get('question')
        opts = item.get('options')
        corr = item.get('correct_answer')
        expl = item.get('explanation')

        if not q or not isinstance(q, str):
            raise ValueError(f'question is required and must be a string at index {idx}')
        if not isinstance(opts, list) or len(opts) < 4:
            raise ValueError(f'options must be a list with at least 4 items at index {idx}')
        if not all(isinstance(o, str) and o.strip() for o in opts):
            raise ValueError(f'all options must be non-empty strings at index {idx}')
        if not corr or not isinstance(corr, str):
            raise ValueError(f'correct_answer is required and must be a string at index {idx}')
        if corr not in opts:
            raise ValueError(f'correct_answer must be one of the options at index {idx}')
        if expl is None or not isinstance(expl, str):
            raise ValueError(f'explanation is required and must be a string at index {idx}')

        normalized.append({
            'question': q.strip(),
            'options': [o.strip() for o in opts],
            'correct_answer': corr.strip(),
            'explanation': expl.strip(),
        })
    return normalized


def generate_ss1_questions(topic: str = '', num_questions: int = 5) -> List[Dict[str, Any]]:
    """Generate SS1-level MCQs and return strictly validated JSON list."""
    if is_gemini_mock_mode():
        logger.warning('Gemini mock mode enabled; generating sample SS1 questions locally.')
        return generate_mock_questions(num_questions=num_questions, topic=topic)

    if not GEMINI_API_KEY:
        raise EnvironmentError('GEMINI_API_KEY is not configured in environment')

    prompt = (
        f"You are an exam question generator for SS1 students. Generate {num_questions} multiple-choice questions suitable for SS1. "
        f"Focus on the topic: {topic}. Return ONLY valid JSON in the format: "
        '[{"question":"", "options":["","","",""], "correct_answer":"", "explanation":""}]'
    )

    last_exc = None
    for attempt in range(1, GEMINI_RETRIES + 1):
        try:
            raw = _make_gemini_request(prompt)
            logger.debug('Raw Gemini response (attempt %s): %s', attempt, raw)
            cleaned = _clean_response_text(raw)
            parsed = _parse_json_from_text(cleaned)
            validated = _validate_strict_questions(parsed)
            logger.info('Gemini SS1 generation succeeded')
            return validated
        except Exception as exc:
            last_exc = exc
            logger.warning('Attempt %s failed: %s', attempt, exc)
            if attempt < GEMINI_RETRIES:
                time.sleep(2 ** (attempt - 1))
            else:
                logger.exception('All Gemini attempts failed')
                raise



def validate_generated_question_payload(question):
    # Import CBTQuestion lazily to avoid AppRegistryNotReady during module import
    global CBTQuestion
    if CBTQuestion is None:
        try:
            from .models import CBTQuestion as _CBTQuestion
            CBTQuestion = _CBTQuestion
        except Exception:
            CBTQuestion = None

    if not isinstance(question, dict):
        return False, 'Each question must be an object.'

    prompt = question.get('prompt')
    if not prompt or not isinstance(prompt, str):
        return False, 'Question prompt is required and must be a string.'

    question_type = question.get('question_type')
    if CBTQuestion is None:
        # If model import failed, perform basic validation only
        if not question_type:
            return False, f'Invalid question_type {question_type}.'
    else:
        if question_type not in dict(CBTQuestion.QUESTION_TYPE_CHOICES):
            return False, f'Invalid question_type {question_type}.'

    try:
        mark_value = float(question.get('mark_value', 1.0))
    except (TypeError, ValueError):
        return False, 'mark_value must be a number.'
    if mark_value <= 0:
        return False, 'mark_value must be greater than zero.'

    difficulty_value = question.get('difficulty')
    if difficulty_value not in dict(CBTQuestion.DIFFICULTY_CHOICES):
        return False, f'Invalid difficulty {difficulty_value}.'

    explanation = question.get('explanation')
    if explanation is None:
        question['explanation'] = ''
    elif not isinstance(explanation, str):
        return False, 'explanation must be a string.'

    topic_value = question.get('topic')
    if topic_value is None:
        question['topic'] = ''
    elif not isinstance(topic_value, str):
        return False, 'topic must be a string.'

    choices = question.get('choices', [])
    if question_type in [CBTQuestion.MCQ, CBTQuestion.MULTIPLE, CBTQuestion.TRUE_FALSE]:
        if not isinstance(choices, list) or len(choices) < 2:
            return False, 'Choice-based questions must include at least two choices.'

        if question_type == CBTQuestion.TRUE_FALSE:
            lower_texts = [str(c.get('text', '')).strip().lower() for c in choices]
            if 'true' not in lower_texts or 'false' not in lower_texts:
                return False, 'True/False questions must include both True and False options.'

        if not any(bool(c.get('is_correct')) for c in choices):
            return False, 'At least one choice must be marked correct.'

        for idx, choice in enumerate(choices):
            if not isinstance(choice, dict):
                return False, 'Each choice must be an object.'
            if not choice.get('text') or not isinstance(choice.get('text'), str):
                return False, 'Each choice must include text.'
            if not isinstance(choice.get('is_correct', False), bool):
                return False, 'Choice is_correct must be boolean.'
            choice['order'] = int(choice.get('order', idx))
    else:
        if choices and not isinstance(choices, list):
            return False, 'Short answer question choices must be an array if provided.'
        question['choices'] = []

    return True, None
