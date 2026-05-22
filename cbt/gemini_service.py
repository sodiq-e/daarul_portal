import json
import os
import re

from .models import CBTQuestion

try:
    from google import genai
    from google.genai.types import GenerateContentConfig
except ImportError:  # pragma: no cover
    genai = None
    GenerateContentConfig = None

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')


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
    if genai is None or GenerateContentConfig is None:
        raise ImportError(
            'Gemini integration requires the google-genai package. '
            'Install google-genai and restart the app.'
        )
    if not GEMINI_API_KEY:
        raise EnvironmentError(
            'Gemini API key is not configured. Set GEMINI_API_KEY in environment.'
        )

    client = genai.Client(api_key=GEMINI_API_KEY)
    config = GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        max_output_tokens=1200,
        candidate_count=1,
    )
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=config,
    )

    text = getattr(response, 'text', None)
    if not text:
        raise ValueError('No text returned from Gemini API')
    return text


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
