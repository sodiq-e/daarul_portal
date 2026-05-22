import json
import os
import re
import urllib.error
import urllib.request

from .models import CBTQuestion

GEMINI_API_URL = os.getenv('GEMINI_API_URL', 'https://api.openai.com/v1/chat/completions')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gpt-4.1-mini')


def _build_prompt(exam, topic, difficulty, num_questions):
    subject_name = getattr(exam.subject, 'name', 'General Knowledge')
    exam_mode = exam.get_exam_mode_display() if hasattr(exam, 'get_exam_mode_display') else 'Exam'
    prompt = (
        f"Generate {num_questions} CBT-style exam questions for a {exam_mode} in {subject_name}. "
        f"Use a clear question prompt, include a topic and difficulty, and return valid JSON only. "
        f"The questions should be appropriate for difficulty level '{difficulty}' and should include an explanation and answer choices when relevant. "
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


def _make_gemini_request(prompt):
    if not GEMINI_API_KEY:
        raise EnvironmentError('Gemini API key is not configured. Set GEMINI_API_KEY in environment.')
    if not GEMINI_API_URL:
        raise EnvironmentError('Gemini API URL is not configured. Set GEMINI_API_URL in environment.')

    payload = {
        'model': GEMINI_MODEL,
        'messages': [
            {'role': 'system', 'content': 'You are a helpful question generation assistant.'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.2,
        'max_tokens': 1200,
        'top_p': 0.95,
        'n': 1,
    }

    data = json.dumps(payload).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GEMINI_API_KEY}',
    }

    request = urllib.request.Request(GEMINI_API_URL, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_body = response.read().decode('utf-8')
            parsed = json.loads(response_body)
            choices = parsed.get('choices') or []
            if not choices:
                raise ValueError('No choices returned from Gemini API')
            message = choices[0].get('message') or choices[0].get('text') or ''
            if isinstance(message, dict):
                message = message.get('content', '')
            return message
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode('utf-8', errors='ignore')
        raise RuntimeError(f'Gemini API request failed: {exc.code} {exc.reason}. Response: {error_body}')
    except urllib.error.URLError as exc:
        raise RuntimeError(f'Gemini API network error: {exc.reason}')


def generate_ai_questions_using_gemini(exam, topic, difficulty, num_questions):
    prompt = _build_prompt(exam, topic, difficulty, num_questions)
    response_text = _make_gemini_request(prompt)
    parsed = _parse_json_from_text(response_text)
    if not isinstance(parsed, list):
        raise ValueError('Gemini response JSON must be an array of questions.')
    return parsed


def validate_generated_question_payload(question):
    if not isinstance(question, dict):
        return False, 'Each question must be an object.'

    prompt = question.get('prompt')
    if not prompt or not isinstance(prompt, str):
        return False, 'Question prompt is required and must be a string.'

    question_type = question.get('question_type')
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
