from datetime import timedelta
from django.utils import timezone
from .models import CBTChoice, CBTStudentAttempt, CBTAnswer, CBTQuestion, StudentAttemptQuestion, QuestionBank
import random
import json
import hashlib


def generate_attempt_seed(attempt_uuid, salt=''):
    """Generate a deterministic seed from attempt UUID for consistent randomization"""
    combined = f"{str(attempt_uuid)}{salt}"
    hash_obj = hashlib.md5(combined.encode())
    return int(hash_obj.hexdigest()[:8], 16)


def get_questions_for_exam(exam):
    """Get questions to display for an exam based on selection mode"""
    if exam.question_mode == exam.QUESTION_MODE_RANDOM and exam.question_bank:
        questions = exam.question_bank.questions.filter(is_active=True)
    else:
        questions = exam.questions.filter(is_active=True)
    return questions


def select_random_questions(questions, total_to_display, seed=None):
    """Select random questions with optional difficulty/topic balancing"""
    if not questions.exists():
        return []
    
    if total_to_display is None or total_to_display >= questions.count():
        return list(questions.order_by('?'))
    
    if seed is not None:
        random.seed(seed)
    
    return random.sample(list(questions), min(total_to_display, questions.count()))


def shuffle_choices_for_question(question, seed=None):
    """Randomize choice order for a question"""
    choices = list(question.choices.all())
    if seed is not None:
        random.seed(seed)
    random.shuffle(choices)
    return [c.id for c in choices]


def create_attempt_with_randomization(exam, student=None, session_key=None):
    """
    Create a student attempt with randomized questions and options.
    Maintains consistency using attempt UUID as seed.
    """
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
    
    # Generate questions for this attempt
    questions = get_questions_for_exam(exam)
    
    # Apply random selection if configured
    if exam.question_mode == exam.QUESTION_MODE_RANDOM:
        total_to_display = exam.total_questions_to_display or questions.count()
        seed = generate_attempt_seed(attempt.uuid, salt='questions')
        questions = select_random_questions(questions, total_to_display, seed=seed)
    else:
        questions = list(questions.order_by('order'))
    
    # Create StudentAttemptQuestion records with randomization
    for position, question in enumerate(questions, start=1):
        # Generate randomized choice order if configured
        randomized_choice_order = []
        if exam.randomize_answers:
            seed = generate_attempt_seed(attempt.uuid, salt=f'question_{question.id}_choices')
            randomized_choice_order = shuffle_choices_for_question(question, seed=seed)
        
        StudentAttemptQuestion.objects.create(
            attempt=attempt,
            question=question,
            randomized_position=position,
            randomized_choice_order=json.dumps(randomized_choice_order) if randomized_choice_order else ''
        )
    
    return attempt


def create_attempt(exam, student=None, session_key=None):
    """Legacy wrapper for backward compatibility"""
    return create_attempt_with_randomization(exam, student=student, session_key=session_key)



def save_answer(attempt, question, selected_choice=None, text_answer=''):
    answer, _created = CBTAnswer.objects.get_or_create(
        attempt=attempt,
        question=question,
        defaults={'text_answer': text_answer or '', 'selected_choices': ''},
    )

    # Handle multiple-select (list of ids) or single selected_choice
    if isinstance(selected_choice, (list, tuple)):
        # store json list
        answer.selected_choices = json.dumps([int(x) for x in selected_choice])
        # determine correctness: all selected choices must match correct set
        correct_ids = [c.id for c in question.choices.filter(is_correct=True)]
        selected_ids = [int(x) for x in selected_choice]
        is_all_correct = set(selected_ids) == set(correct_ids)
        answer.is_correct = is_all_correct
        answer.awarded_marks = question.mark_value if is_all_correct else 0
        answer.selected_choice = None
    else:
        # single choice or None
        answer.selected_choice = selected_choice
        answer.selected_choices = ''
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

        if question.question_type in (question.MCQ, question.TRUE_FALSE):
            if answer.selected_choice and answer.selected_choice.is_correct:
                earned += float(question.mark_value)
                answer.is_correct = True
                answer.awarded_marks = question.mark_value
            else:
                answer.is_correct = False
                answer.awarded_marks = 0
        elif question.question_type == question.MULTIPLE:
            # multiple-select: check selected_choices JSON
            try:
                sel = json.loads(answer.selected_choices) if answer.selected_choices else []
            except Exception:
                sel = []
            correct_ids = [c.id for c in question.choices.filter(is_correct=True)]
            if set(sel) == set(correct_ids) and sel:
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
    attempt_questions = attempt.attempt_questions.select_related('question').prefetch_related('question__choices').order_by('randomized_position')
    answers = attempt.answers.select_related('selected_choice').all()
    answers_by_question = {answer.question_id: answer for answer in answers}

    question_context = []
    total_points = 0
    for aq in attempt_questions:
        q = aq.question
        total_points += float(q.mark_value)
        answer = answers_by_question.get(q.id)

        selected_choice = answer.selected_choice if answer else None
        selected_choice_ids = []
        selected_text = ''
        if answer:
            if answer.selected_choices:
                try:
                    selected_choice_ids = json.loads(answer.selected_choices)
                except Exception:
                    selected_choice_ids = []
            selected_text = answer.text_answer or ''

        choices = aq.get_randomized_choices() if aq.randomized_choice_order else list(q.choices.all().order_by('order'))
        correct_choices = [choice for choice in choices if choice.is_correct]

        question_context.append({
            'attempt_question': aq,
            'question': q,
            'choices': choices,
            'answer': answer,
            'selected_choice': selected_choice,
            'selected_choice_ids': selected_choice_ids,
            'selected_text': selected_text,
            'correct_choices': correct_choices,
            'is_correct': bool(answer and answer.is_correct),
            'awarded_marks': float(answer.awarded_marks) if answer else 0,
            'mark_value': float(q.mark_value),
        })

    return {
        'attempt': attempt,
        'exam': attempt.exam,
        'questions': question_context,
        'time_left_seconds': max(0, int((attempt.started_at + timedelta(minutes=attempt.exam.duration_minutes) - timezone.now()).total_seconds())),
        'total_points': total_points,
    }


def generate_ai_question_stub(exam, count=5):
    raise NotImplementedError('AI question generation will be added in a later phase.')
