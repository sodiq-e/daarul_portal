from datetime import timedelta
from django.utils import timezone
from .models import CBTChoice, CBTStudentAttempt, CBTAnswer


def create_attempt(exam, student=None, session_key=None):
    if exam.is_real_exam() and student is None:
        raise ValueError('Real exams require authenticated student access.')
    if not student and not session_key:
        raise ValueError('Practice attempts require a session key.')

    attempt = CBTStudentAttempt.objects.create(
        exam=exam,
        student=student,
        session_key=session_key,
        started_at=timezone.now(),
        last_saved_at=timezone.now(),
    )
    return attempt


def save_answer(attempt, question, selected_choice=None, text_answer=''):
    answer, _created = CBTAnswer.objects.get_or_create(
        attempt=attempt,
        question=question,
        defaults={'text_answer': text_answer or ''},
    )

    answer.selected_choice = selected_choice
    answer.text_answer = text_answer or ''

    if selected_choice is not None:
        answer.is_correct = selected_choice.is_correct
        answer.awarded_marks = question.mark_value if selected_choice.is_correct else 0
    else:
        answer.is_correct = False
        answer.awarded_marks = 0

    answer.save()
    attempt.last_saved_at = timezone.now()
    attempt.save(update_fields=['last_saved_at'])
    return answer


def grade_attempt(attempt):
    earned = 0
    total = 0
    for question in attempt.exam.questions.filter(is_active=True).prefetch_related('choices'):
        total += float(question.mark_value)
        try:
            answer = attempt.answers.get(question=question)
        except CBTAnswer.DoesNotExist:
            continue

        if question.question_type == question.MCQ or question.question_type == question.TRUE_FALSE:
            if answer.selected_choice and answer.selected_choice.is_correct:
                earned += float(question.mark_value)
                answer.is_correct = True
                answer.awarded_marks = question.mark_value
            else:
                answer.is_correct = False
                answer.awarded_marks = 0
        else:
            # Short answer grading may be manual or AI-assisted in future.
            answer.is_correct = False
            answer.awarded_marks = 0

        answer.save(update_fields=['is_correct', 'awarded_marks'])

    attempt.score = earned
    attempt.is_scored = True
    attempt.completed_at = timezone.now()
    attempt.is_submitted = True
    attempt.save(update_fields=['score', 'is_scored', 'completed_at', 'is_submitted'])
    return attempt


def build_attempt_context(attempt):
    questions = attempt.exam.questions.filter(is_active=True).order_by('order')
    answers = attempt.answers.select_related('selected_choice').all()
    answer_map = {answer.question_id: answer.selected_choice_id for answer in answers if answer.selected_choice_id}
    total_points = sum(float(question.mark_value) for question in questions)

    return {
        'attempt': attempt,
        'exam': attempt.exam,
        'questions': questions,
        'answers_map': answer_map,
        'time_left_seconds': max(0, int((attempt.started_at + timedelta(minutes=attempt.exam.duration_minutes) - timezone.now()).total_seconds())),
        'total_points': total_points,
    }


def generate_ai_question_stub(exam, count=5):
    raise NotImplementedError('AI question generation will be added in a later phase.')
