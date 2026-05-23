import json
import logging
import os
import time

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.db.models import Avg, Q, Count, Max
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import (
    CBTExam,
    CBTQuestion,
    CBTStudentAttempt,
    CBTAnswer,
    CBTChoice,
    QuestionBank,
    StudentAttemptQuestion,
    CBTAttemptIntegrityEvent,
    AIRequestMetric,
)
from .forms import CBTExamForm, CBTQuestionForm, CBTChoiceFormSet
from .services import create_attempt, grade_attempt, save_answer, build_attempt_context
from .gemini_service import (
    generate_ai_questions_using_gemini,
    validate_generated_question_payload,
    generate_ss1_questions,
    GeminiQuotaError,
    GeminiInvalidAPIKeyError,
    GeminiModelNotFoundError,
    GeminiTimeoutError,
    GeminiJSONError,
    GeminiAPIError,
)
import logging
import time
from django.http import JsonResponse, HttpResponseForbidden
import json

AI_GENERATION_THROTTLE_SECONDS = int(os.getenv('AI_GENERATION_THROTTLE_SECONDS', '8'))
AI_GENERATION_SESSION_KEY = 'cbt_ai_generation'


def _increment_ai_generation_failure(request):
    throttle_data = request.session.get(AI_GENERATION_SESSION_KEY, {})
    throttle_data['daily_failed_requests'] = throttle_data.get('daily_failed_requests', 0) + 1
    request.session[AI_GENERATION_SESSION_KEY] = throttle_data
    request.session.modified = True


def is_cbt_teacher(user):
    try:
        return user.profile.is_approved and user.groups.filter(name__in=['Teacher', 'Staff']).exists()
    except Exception:
        return user.is_staff


def is_cbt_authenticated(user):
    try:
        return user.profile.is_approved
    except Exception:
        return user.is_authenticated


def is_cbt_student(user):
    try:
        return user.profile.is_approved and hasattr(user, 'student_profile')
    except Exception:
        return False


@method_decorator(login_required, name='dispatch')
class CBTExamListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = CBTExam
    template_name = 'cbt/exam_list.html'
    context_object_name = 'exams'
    paginate_by = 20

    def test_func(self):
        return is_cbt_teacher(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exam_mode_choices'] = CBTExam.EXAM_MODE_CHOICES
        return context


@method_decorator(login_required, name='dispatch')
class CBTExamCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = CBTExam
    form_class = CBTExamForm
    template_name = 'cbt/exam_form.html'
    success_url = reverse_lazy('cbt:exam_list')

    def test_func(self):
        return is_cbt_teacher(self.request.user)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'CBT exam created successfully.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class CBTExamUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CBTExam
    form_class = CBTExamForm
    template_name = 'cbt/exam_form.html'
    success_url = reverse_lazy('cbt:exam_list')

    def test_func(self):
        return is_cbt_teacher(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'CBT exam updated successfully.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class CBTQuestionListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'cbt/question_list.html'

    def test_func(self):
        return is_cbt_teacher(self.request.user)

    def get_context_data(self, **kwargs):
        exam = get_object_or_404(CBTExam, pk=self.kwargs.get('exam_pk'))
        return {
            'exam': exam,
            'questions': exam.questions.all(),
        }


@method_decorator(login_required, name='dispatch')
class CBTQuestionCreateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'cbt/question_form.html'

    def test_func(self):
        return is_cbt_teacher(self.request.user)

    def get(self, request, *args, **kwargs):
        exam = get_object_or_404(CBTExam, pk=self.kwargs.get('exam_pk'))
        form = CBTQuestionForm()
        formset = CBTChoiceFormSet()
        return render(request, self.template_name, {'exam': exam, 'form': form, 'formset': formset})

    def post(self, request, *args, **kwargs):
        exam = get_object_or_404(CBTExam, pk=self.kwargs.get('exam_pk'))
        form = CBTQuestionForm(request.POST)
        formset = CBTChoiceFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            question = form.save(commit=False)
            question.exam = exam
            question.save()
            formset.instance = question
            formset.save()
            messages.success(request, 'Question created successfully.')
            return redirect('cbt:question_list', exam_pk=exam.pk)
        return render(request, self.template_name, {'exam': exam, 'form': form, 'formset': formset})


@method_decorator(login_required, name='dispatch')
class CBTQuestionUpdateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'cbt/question_form.html'

    def test_func(self):
        return is_cbt_teacher(self.request.user)

    def get(self, request, *args, **kwargs):
        question = get_object_or_404(CBTQuestion, pk=self.kwargs.get('question_pk'))
        form = CBTQuestionForm(instance=question)
        formset = CBTChoiceFormSet(instance=question)
        return render(request, self.template_name, {'exam': question.exam, 'form': form, 'formset': formset, 'question': question})

    def post(self, request, *args, **kwargs):
        question = get_object_or_404(CBTQuestion, pk=self.kwargs.get('question_pk'))
        form = CBTQuestionForm(request.POST, instance=question)
        formset = CBTChoiceFormSet(request.POST, instance=question)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Question updated successfully.')
            return redirect('cbt:question_list', exam_pk=question.exam.pk)
        return render(request, self.template_name, {'exam': question.exam, 'form': form, 'formset': formset, 'question': question})


class PracticeExamListView(TemplateView):
    template_name = 'cbt/practice_exam_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['practice_exams'] = CBTExam.objects.filter(
            exam_mode=CBTExam.PRACTICE,
            is_active=True,
            is_published=True,
        ).order_by('name')
        return context


class RealExamListView(LoginRequiredMixin, ListView):
    model = CBTExam
    template_name = 'cbt/real_exam_list.html'
    context_object_name = 'real_exams'

    def get_queryset(self):
        return CBTExam.objects.filter(
            exam_mode=CBTExam.REAL,
            is_active=True,
            is_published=True,
        ).order_by('name')


@login_required
def real_exam_detail(request, pk):
    exam = get_object_or_404(CBTExam, pk=pk, exam_mode=CBTExam.REAL)
    return render(request, 'cbt/real_exam_detail.html', {'exam': exam})


def _ensure_session(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def start_practice_exam(request, pk):
    exam = get_object_or_404(CBTExam, pk=pk, exam_mode=CBTExam.PRACTICE, is_published=True, is_active=True)
    session_key = _ensure_session(request)
    attempt = create_attempt(exam=exam, session_key=session_key)
    return redirect('cbt:attempt_detail', uuid=attempt.uuid)


@login_required
def start_real_exam(request, pk):
    exam = get_object_or_404(CBTExam, pk=pk, exam_mode=CBTExam.REAL, is_published=True, is_active=True)
    attempt = create_attempt(exam=exam, student=request.user)
    return redirect('cbt:attempt_detail', uuid=attempt.uuid)


def attempt_detail(request, uuid):
    attempt = get_object_or_404(CBTStudentAttempt, uuid=uuid)
    if attempt.is_submitted:
        context = build_attempt_context(attempt)
        return render(request, 'cbt/attempt_result.html', context)

    if request.method == 'POST':
        for question in attempt.exam.questions.filter(is_active=True):
            answer_field = request.POST.get(f'question_{question.pk}')
            selected_choice = None
            text_answer = ''
            if question.question_type in [CBTQuestion.MCQ, CBTQuestion.TRUE_FALSE]:
                try:
                    selected_choice = CBTChoice.objects.get(pk=int(answer_field), question=question)
                except (ValueError, CBTChoice.DoesNotExist, TypeError):
                    selected_choice = None
            else:
                text_answer = answer_field or ''
            save_answer(attempt=attempt, question=question, selected_choice=selected_choice, text_answer=text_answer)
        grade_attempt(attempt)
        messages.success(request, 'Exam submitted and graded. Your score has been recorded.')
        return redirect('cbt:attempt_detail', uuid=attempt.uuid)

    context = build_attempt_context(attempt)
    # Build JSON payload for frontend
    # Use attempt.attempt_questions ordering if available
    attempt_questions = attempt.attempt_questions.select_related('question').prefetch_related('question__choices').order_by('randomized_position')
    questions_list = []
    answers = {a.question_id: a for a in attempt.answers.select_related('selected_choice').all()}
    for aq in attempt_questions:
        q = aq.question
        # build choices in randomized order if present
        if aq.randomized_choice_order:
            try:
                order_ids = json.loads(aq.randomized_choice_order)
            except Exception:
                order_ids = []
            choices_qs = list(q.choices.all())
            choices_map = {c.id: c for c in choices_qs}
            choices = [
                {'id': cid, 'text': choices_map[cid].text} for cid in order_ids if cid in choices_map
            ]
            # append any missing choices
            for c in choices_qs:
                if c.id not in order_ids:
                    choices.append({'id': c.id, 'text': c.text})
        else:
            choices = [{'id': c.id, 'text': c.text} for c in q.choices.all().order_by('order')]

        ans = answers.get(q.id)
        answer_payload = None
        if ans:
            try:
                sel_multi = json.loads(ans.selected_choices) if ans.selected_choices else []
            except Exception:
                sel_multi = []
            answer_payload = {
                'selected_choice_id': ans.selected_choice_id,
                'selected_choice_ids': sel_multi,
                'text_answer': ans.text_answer,
            }

        questions_list.append({
            'id': q.id,
            'prompt': q.prompt,
            'question_type': q.question_type,
            'mark_value': float(q.mark_value),
            'topic': getattr(q, 'topic', ''),
            'difficulty': getattr(q, 'difficulty', ''),
            'choices': choices,
        })

    # inject JSON into context for template
    context['questions_json'] = json.dumps(questions_list)
    # build answers array aligned by position
    answers_arr = []
    for aq in attempt_questions:
        qid = aq.question.id
        a = answers.get(qid)
        if a:
            try:
                sel_multi = json.loads(a.selected_choices) if a.selected_choices else []
            except Exception:
                sel_multi = []
            answers_arr.append({
                'question_id': qid,
                'selected_choice_id': a.selected_choice_id,
                'selected_choice_ids': sel_multi,
                'text_answer': a.text_answer,
            })
        else:
            answers_arr.append(None)

    context['answers_json'] = json.dumps(answers_arr)
    context['flagged_questions_json'] = json.dumps(list(attempt_questions.filter(is_flagged=True).values_list('randomized_position', flat=True)))
    context['total_questions'] = attempt.attempt_questions.count() or attempt.exam.questions.filter(is_active=True).count()
    # Determine remaining time for the current attempt
    elapsed_seconds = max(0, int((timezone.now() - attempt.started_at).total_seconds()))
    total_seconds = int(attempt.exam.duration_minutes * 60)
    context['time_left_seconds'] = max(0, total_seconds - elapsed_seconds)
    return render(request, 'cbt/student_attempt_view.html', context)


@login_required
def api_save_answer(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    try:
        data = json.loads(request.body.decode())
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    attempt_uuid = data.get('attempt_uuid')
    question_id = data.get('question_id')
    selected_choice = data.get('selected_choice_id')
    selected_choice_ids = data.get('selected_choice_ids')
    text_answer = data.get('text_answer', '')

    attempt = get_object_or_404(CBTStudentAttempt, uuid=attempt_uuid)
    # permission check
    if attempt.student and attempt.student != request.user:
        return HttpResponseForbidden()
    if attempt.is_submitted:
        return JsonResponse({'error': 'attempt already submitted'}, status=400)

    # Verify question belongs to the exam
    question = get_object_or_404(CBTQuestion, pk=question_id, exam=attempt.exam)
    
    # handle answer updates only when answer data is present
    has_answer_data = selected_choice_ids is not None or selected_choice is not None or (text_answer and text_answer.strip());
    if has_answer_data:
        if selected_choice_ids is not None:
            save_answer(attempt=attempt, question=question, selected_choice=selected_choice_ids, text_answer='')
        else:
            sel_choice_obj = None
            if selected_choice:
                try:
                    sel_choice_obj = CBTChoice.objects.get(pk=int(selected_choice), question=question)
                except CBTChoice.DoesNotExist:
                    return JsonResponse({'error': 'invalid choice for this question'}, status=400)
            save_answer(attempt=attempt, question=question, selected_choice=sel_choice_obj, text_answer=text_answer)

    if 'is_flagged' in data:
        is_flagged = bool(data.get('is_flagged'))
        saq = StudentAttemptQuestion.objects.filter(attempt=attempt, question=question).first()
        if saq:
            saq.is_flagged = is_flagged
            saq.save(update_fields=['is_flagged'])

    integrity_events = data.get('integrity_events')
    if isinstance(integrity_events, list) and integrity_events:
        for event in integrity_events:
            if not isinstance(event, dict):
                continue
            reason = event.get('reason') or 'unknown'
            metadata = event.get('metadata') if isinstance(event.get('metadata'), dict) else {}
            CBTAttemptIntegrityEvent.objects.create(
                attempt=attempt,
                reason=reason,
                metadata=metadata
            )

    return JsonResponse({'status': 'saved', 'last_saved': attempt.last_saved_at.isoformat()})


@csrf_exempt
@login_required
def api_submit_attempt(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    attempt_uuid = None
    body = request.body.decode(errors='ignore')
    if body:
        try:
            data = json.loads(body)
            attempt_uuid = data.get('attempt_uuid')
        except Exception:
            pass

    if not attempt_uuid:
        attempt_uuid = request.POST.get('attempt_uuid') or request.GET.get('attempt_uuid')

    if not attempt_uuid:
        return JsonResponse({'error': 'attempt_uuid required'}, status=400)

    # Enforce same-origin for beacon/fallback submissions
    origin = request.META.get('HTTP_ORIGIN')
    referer = request.META.get('HTTP_REFERER')
    allowed_origin = f"{request.scheme}://{request.get_host()}"
    if origin and origin != allowed_origin:
        return HttpResponseForbidden()
    if not origin and referer and not referer.startswith(allowed_origin):
        return HttpResponseForbidden()

    attempt = get_object_or_404(CBTStudentAttempt, uuid=attempt_uuid)
    if attempt.student and attempt.student != request.user:
        return HttpResponseForbidden()
    if attempt.is_submitted:
        return JsonResponse({'error': 'already submitted'}, status=400)

    # grade and finalize
    grade_attempt(attempt)
    return JsonResponse({'status': 'submitted', 'score': float(attempt.score or 0)})


@login_required
def api_generate_ai_questions(request, exam_pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    exam = get_object_or_404(CBTExam, pk=exam_pk, created_by=request.user)
    if not exam.allow_ai_questions:
        return JsonResponse({'error': 'AI question generation is not enabled for this exam.'}, status=403)

    try:
        data = json.loads(request.body.decode())
    except Exception:
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

    now_ts = int(time.time())
    throttle_data = request.session.get(AI_GENERATION_SESSION_KEY, {})
    last_request_ts = throttle_data.get('last_request_at', 0)
    if now_ts - last_request_ts < AI_GENERATION_THROTTLE_SECONDS:
        return JsonResponse({
            'error': 'Please wait a few seconds before generating questions again. Reduce repeated requests and try again shortly.'
        }, status=429)

    throttle_data['last_request_at'] = now_ts
    throttle_data['daily_request_count'] = throttle_data.get('daily_request_count', 0) + 1
    throttle_data.setdefault('daily_successful_requests', 0)
    throttle_data.setdefault('daily_failed_requests', 0)
    request.session[AI_GENERATION_SESSION_KEY] = throttle_data
    request.session.modified = True

    topic = data.get('topic', '').strip()
    difficulty = data.get('difficulty', CBTQuestion.DIFFICULTY_MEDIUM)
    num_questions = data.get('num_questions', 5)
    try:
        num_questions = int(num_questions)
    except (TypeError, ValueError):
        num_questions = 5

    if num_questions < 1 or num_questions > 20:
        return JsonResponse({'error': 'num_questions must be between 1 and 20.'}, status=400)

    if difficulty not in dict(CBTQuestion.DIFFICULTY_CHOICES):
        return JsonResponse({'error': 'Invalid difficulty value.'}, status=400)

    try:
        start_ts = time.time()
        questions = generate_ai_questions_using_gemini(exam=exam, topic=topic, difficulty=difficulty, num_questions=num_questions)
        latency_ms = int((time.time() - start_ts) * 1000)
        throttle_data['daily_successful_requests'] = throttle_data.get('daily_successful_requests', 0) + 1
        request.session[AI_GENERATION_SESSION_KEY] = throttle_data
        request.session.modified = True
        AIRequestMetric.objects.create(
            user=request.user,
            exam=exam,
            request_type=AIRequestMetric.REQUEST_TYPE_GENERATE_AI,
            status=AIRequestMetric.STATUS_SUCCESS,
            latency_ms=latency_ms,
        )
    except GeminiQuotaError as exc:
        _increment_ai_generation_failure(request)
        AIRequestMetric.objects.create(
            user=request.user,
            exam=exam,
            request_type=AIRequestMetric.REQUEST_TYPE_GENERATE_AI,
            status=AIRequestMetric.STATUS_QUOTA,
            error_code=exc.__class__.__name__,
        )
        return JsonResponse({
            'error': str(exc),
            'retryable': True,
        }, status=503)
    except GeminiInvalidAPIKeyError as exc:
        _increment_ai_generation_failure(request)
        AIRequestMetric.objects.create(
            user=request.user,
            exam=exam,
            request_type=AIRequestMetric.REQUEST_TYPE_GENERATE_AI,
            status=AIRequestMetric.STATUS_FAILURE,
            error_code=exc.__class__.__name__,
        )
        return JsonResponse({'error': str(exc)}, status=401)
    except GeminiModelNotFoundError as exc:
        _increment_ai_generation_failure(request)
        AIRequestMetric.objects.create(
            user=request.user,
            exam=exam,
            request_type=AIRequestMetric.REQUEST_TYPE_GENERATE_AI,
            status=AIRequestMetric.STATUS_FAILURE,
            error_code=exc.__class__.__name__,
        )
        return JsonResponse({'error': str(exc)}, status=404)
    except GeminiTimeoutError as exc:
        _increment_ai_generation_failure(request)
        AIRequestMetric.objects.create(
            user=request.user,
            exam=exam,
            request_type=AIRequestMetric.REQUEST_TYPE_GENERATE_AI,
            status=AIRequestMetric.STATUS_FAILURE,
            error_code=exc.__class__.__name__,
        )
        return JsonResponse({'error': str(exc), 'retryable': True}, status=503)
    except GeminiJSONError as exc:
        _increment_ai_generation_failure(request)
        AIRequestMetric.objects.create(
            user=request.user,
            exam=exam,
            request_type=AIRequestMetric.REQUEST_TYPE_GENERATE_AI,
            status=AIRequestMetric.STATUS_FAILURE,
            error_code=exc.__class__.__name__,
        )
        return JsonResponse({'error': 'The AI returned an unexpected response format. Please try again or contact support.'}, status=502)
    except GeminiAPIError as exc:
        _increment_ai_generation_failure(request)
        AIRequestMetric.objects.create(
            user=request.user,
            exam=exam,
            request_type=AIRequestMetric.REQUEST_TYPE_GENERATE_AI,
            status=AIRequestMetric.STATUS_FAILURE,
            error_code=exc.__class__.__name__,
        )
        return JsonResponse({'error': str(exc)}, status=500)
    except Exception as exc:
        _increment_ai_generation_failure(request)
        AIRequestMetric.objects.create(
            user=request.user,
            exam=exam,
            request_type=AIRequestMetric.REQUEST_TYPE_GENERATE_AI,
            status=AIRequestMetric.STATUS_FAILURE,
            error_code=exc.__class__.__name__,
        )
        return JsonResponse({'error': 'AI generation failed. Please try again later.'}, status=500)

    validated_questions = []
    for question in questions:
        valid, error = validate_generated_question_payload(question)
        if not valid:
            return JsonResponse({'error': f'AI returned invalid question data: {error}'}, status=500)
        validated_questions.append(question)

    return JsonResponse({'status': 'ok', 'questions': validated_questions})


@login_required
def api_ai_request_metrics(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'GET required'}, status=400)

    metrics = AIRequestMetric.objects.filter(exam__created_by=request.user)
    today = timezone.localdate()
    summary = list(metrics.values('request_type', 'status').annotate(count=Count('id')))
    today_summary = list(metrics.filter(date=today).values('status').annotate(count=Count('id')))
    return JsonResponse({
        'metrics': summary,
        'today': today_summary,
    })


@login_required
def api_generate_ss1_questions(request):
    """
    Test endpoint for generating SS1 questions from Gemini.

    - Validates GEMINI_API_KEY presence
    - Calls `generate_ss1_questions` which performs cleaning, retries and strict validation
    - Returns ONLY the list of question objects on success (safe=False)
    - On error returns a fallback JSON: {"success": false, "error": "message"}

    Note: This endpoint is for testing the AI integration only. Do NOT wire
    frontend UI to this endpoint until SDK, parsing and validation are confirmed.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=400)

    try:
        data = json.loads(request.body.decode() or '{}')
    except Exception:
        return JsonResponse({'success': False, 'error': 'Invalid JSON payload.'}, status=400)

    topic = data.get('topic', '').strip()
    num_questions = data.get('num_questions', 5)
    try:
        num_questions = int(num_questions)
    except (TypeError, ValueError):
        num_questions = 5

    if num_questions < 1 or num_questions > 20:
        return JsonResponse({'success': False, 'error': 'num_questions must be between 1 and 20.'}, status=400)

    try:
        questions = generate_ss1_questions(topic=topic, num_questions=num_questions)
    except EnvironmentError as env_err:
        logging.exception('Environment error when generating SS1 questions')
        return JsonResponse({'success': False, 'error': str(env_err)}, status=500)
    except GeminiQuotaError as exc:
        logging.warning('Gemini quota error for SS1 generation: %s', exc)
        return JsonResponse({'success': False, 'error': str(exc)}, status=503)
    except GeminiInvalidAPIKeyError as exc:
        logging.warning('Gemini auth error for SS1 generation: %s', exc)
        return JsonResponse({'success': False, 'error': str(exc)}, status=401)
    except GeminiModelNotFoundError as exc:
        logging.warning('Gemini model error for SS1 generation: %s', exc)
        return JsonResponse({'success': False, 'error': str(exc)}, status=404)
    except GeminiTimeoutError as exc:
        logging.warning('Gemini timeout for SS1 generation: %s', exc)
        return JsonResponse({'success': False, 'error': str(exc)}, status=503)
    except GeminiJSONError as exc:
        logging.warning('Gemini JSON format error for SS1 generation: %s', exc)
        return JsonResponse({'success': False, 'error': 'The AI returned an unexpected response format. Please try again later.'}, status=502)
    except GeminiAPIError as exc:
        logging.warning('Gemini API error for SS1 generation: %s', exc)
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)
    except Exception as exc:
        logging.exception('Failed to generate SS1 questions')
        return JsonResponse({'success': False, 'error': 'AI generation failed: ' + str(exc)}, status=500)

    # Return the validated list directly (safe=False allows non-dict top-level JSON)
    return JsonResponse(questions, safe=False)


@login_required
def api_save_generated_ai_questions(request, exam_pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    exam = get_object_or_404(CBTExam, pk=exam_pk, created_by=request.user)
    if not exam.allow_ai_questions:
        return JsonResponse({'error': 'AI question generation is not enabled for this exam.'}, status=403)

    try:
        data = json.loads(request.body.decode())
    except Exception:
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

    questions = data.get('questions')
    if not isinstance(questions, list) or not questions:
        return JsonResponse({'error': 'questions must be a non-empty list.'}, status=400)

    created_question_ids = []
    try:
        with transaction.atomic():
            current_max_order = exam.questions.aggregate(max_order=Max('order'))['max_order']
            if current_max_order is None:
                current_max_order = -1

            for idx, question in enumerate(questions):
                valid, error = validate_generated_question_payload(question)
                if not valid:
                    return JsonResponse({'error': f'Invalid question payload at index {idx}: {error}'}, status=400)

                qobj = CBTQuestion.objects.create(
                    exam=exam,
                    question_bank=None,
                    prompt=question['prompt'].strip(),
                    question_type=question['question_type'],
                    mark_value=question.get('mark_value', 1.0),
                    explanation=question.get('explanation', '').strip(),
                    topic=question.get('topic', '').strip(),
                    difficulty=question['difficulty'],
                    order=current_max_order + idx + 1,
                    is_active=True
                )

                for cidx, choice in enumerate(question.get('choices', [])):
                    CBTChoice.objects.create(
                        question=qobj,
                        text=choice['text'].strip(),
                        is_correct=bool(choice.get('is_correct', False)),
                        order=cidx
                    )

                created_question_ids.append(qobj.id)
    except Exception as exc:
        return JsonResponse({'error': f'Failed to save generated questions: {str(exc)}'}, status=500)

    return JsonResponse({'status': 'ok', 'created_question_ids': created_question_ids})


@method_decorator(login_required, name='dispatch')
class StudentCBTDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'cbt/student_dashboard.html'

    def test_func(self):
        return is_cbt_student(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        # include attempts either owned by the user or tied to the current session
        session_key = _ensure_session(self.request)
        context['active_attempts'] = CBTStudentAttempt.objects.filter(
            (Q(student=self.request.user) | Q(session_key=session_key)),
            is_submitted=False
        ).select_related('exam').order_by('-started_at')
        # provide explicit counts to make templates defensive and straightforward
        context['active_attempts_count'] = context['active_attempts'].count()
        context['recent_cbt_results'] = CBTStudentAttempt.objects.filter(
            (Q(student=self.request.user) | Q(session_key=session_key)),
            is_submitted=True
        ).select_related('exam').order_by('-completed_at')[:5]
        context['recent_cbt_results_count'] = CBTStudentAttempt.objects.filter((Q(student=self.request.user) | Q(session_key=session_key)), is_submitted=True).count()
        student_class = getattr(getattr(self.request.user, 'student_profile', None), 'student_class', None)
        if student_class:
            context['upcoming_cbt_exams'] = CBTExam.objects.filter(
                exam_mode=CBTExam.REAL,
                is_active=True,
                is_published=True,
                start_datetime__gt=now,
                school_class=student_class
            ).order_by('start_datetime')
            context['upcoming_cbt_exams_count'] = context['upcoming_cbt_exams'].count()
        else:
            context['upcoming_cbt_exams'] = CBTExam.objects.none()
            context['upcoming_cbt_exams_count'] = 0
        return context


@method_decorator(login_required, name='dispatch')
class StudentCBTPracticeListView(LoginRequiredMixin, UserPassesTestMixin, PracticeExamListView):
    template_name = 'cbt/student_practice_list.html'

    def test_func(self):
        return is_cbt_student(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_class = getattr(getattr(self.request.user, 'student_profile', None), 'student_class', None)
        if student_class:
            context['practice_exams'] = context['practice_exams'].filter(school_class=student_class)
        return context


@method_decorator(login_required, name='dispatch')
class StudentCBTAttemptListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'cbt/student_attempt_list.html'

    def test_func(self):
        return is_cbt_student(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_key = _ensure_session(self.request)
        context['attempts'] = CBTStudentAttempt.objects.filter(
            (Q(student=self.request.user) | Q(session_key=session_key))
        ).select_related('exam').order_by('-started_at')
        return context


@method_decorator(login_required, name='dispatch')
class StudentCBTResultListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'cbt/student_result_list.html'

    def test_func(self):
        return is_cbt_student(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_key = _ensure_session(self.request)
        context['attempts'] = CBTStudentAttempt.objects.filter(
            (Q(student=self.request.user) | Q(session_key=session_key)),
            is_submitted=True
        ).select_related('exam').order_by('-completed_at')
        return context


@method_decorator(login_required, name='dispatch')
class TeacherCBTDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'cbt/teacher_dashboard.html'

    def test_func(self):
        return is_cbt_teacher(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exams = CBTExam.objects.filter(created_by=self.request.user)
        attempts = CBTStudentAttempt.objects.filter(exam__created_by=self.request.user)
        context['cbt_exams_created'] = exams.count()
        context['cbt_active_exams'] = exams.filter(is_active=True, is_published=True).count()
        context['cbt_attempts'] = attempts.count()
        context['cbt_recent_attempts'] = attempts.select_related('student', 'exam').order_by('-started_at')[:5]
        completed_attempts = attempts.filter(is_submitted=True)
        context['cbt_avg_score'] = completed_attempts.aggregate(avg_score=Avg('score'))['avg_score'] or 0
        return context


@method_decorator(login_required, name='dispatch')
class TeacherCBTExamListView(CBTExamListView):
    template_name = 'cbt/teacher_exam_list.html'

    def get_queryset(self):
        return super().get_queryset().filter(created_by=self.request.user)


@method_decorator(login_required, name='dispatch')
class TeacherCBTExamCreateView(CBTExamCreateView):
    success_url = reverse_lazy('teacher_cbt:manage')


@method_decorator(login_required, name='dispatch')
class TeacherCBTExamUpdateView(CBTExamUpdateView):
    success_url = reverse_lazy('teacher_cbt:manage')


@method_decorator(login_required, name='dispatch')
class TeacherCBTAttemptListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = CBTStudentAttempt
    template_name = 'cbt/teacher_attempt_list.html'
    context_object_name = 'attempts'
    paginate_by = 20

    def test_func(self):
        return is_cbt_teacher(self.request.user)

    def get_queryset(self):
        return CBTStudentAttempt.objects.filter(
            exam__created_by=self.request.user
        ).select_related('exam', 'student').annotate(
            integrity_count=Count('integrity_events')
        ).order_by('-started_at')


@method_decorator(login_required, name='dispatch')
class TeacherCBTAnalyticsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'cbt/teacher_analytics.html'

    def test_func(self):
        return is_cbt_teacher(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exams = CBTExam.objects.filter(created_by=self.request.user)
        attempts = CBTStudentAttempt.objects.filter(exam__created_by=self.request.user, is_submitted=True)
        context['cbt_exams_created'] = exams.count()
        context['cbt_active_exams'] = exams.filter(is_active=True, is_published=True).count()
        context['cbt_attempts'] = attempts.count()
        context['cbt_avg_score'] = attempts.aggregate(avg_score=Avg('score'))['avg_score'] or 0
        today = timezone.localdate()
        ai_metrics = AIRequestMetric.objects.filter(exam__created_by=self.request.user)
        context['ai_metrics_summary'] = ai_metrics.values('request_type', 'status').annotate(count=Count('id'))
        context['ai_metrics_today'] = ai_metrics.filter(date=today).values('status').annotate(count=Count('id'))
        return context


@method_decorator(login_required, name='dispatch')
class TeacherCBTAIGeneratorView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'cbt/ai_question_generator.html'

    def test_func(self):
        return CBTExam.objects.filter(
            pk=self.kwargs.get('exam_pk'),
            created_by=self.request.user,
            allow_ai_questions=True
        ).exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = get_object_or_404(CBTExam, pk=self.kwargs.get('exam_pk'))
        context['exam'] = exam
        context['QUESTION_TYPE_CHOICES'] = CBTQuestion.QUESTION_TYPE_CHOICES
        context['DIFFICULTY_CHOICES'] = CBTQuestion.DIFFICULTY_CHOICES
        return context


class ManageExamQuestionsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Bulk question builder and manager for a specific exam"""
    template_name = 'cbt/manage_exam_questions.html'

    def test_func(self):
        exam = get_object_or_404(CBTExam, pk=self.kwargs.get('exam_pk'))
        return exam.created_by == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = get_object_or_404(CBTExam, pk=self.kwargs.get('exam_pk'))
        # existing questions for the exam
        context['exam'] = exam
        context['questions'] = exam.questions.all().prefetch_related('choices')
        # include question bank options
        context['question_banks'] = QuestionBank.objects.filter(created_by=self.request.user)
        # provide choice lists for template
        context['QUESTION_TYPE_CHOICES'] = CBTQuestion.QUESTION_TYPE_CHOICES
        context['DIFFICULTY_CHOICES'] = CBTQuestion.DIFFICULTY_CHOICES
        return context

    def post(self, request, *args, **kwargs):
        exam = get_object_or_404(CBTExam, pk=self.kwargs.get('exam_pk'))
        if exam.created_by != request.user:
            return HttpResponseForbidden()

        payload = {}
        if request.content_type and 'application/json' in request.content_type:
            try:
                payload = json.loads(request.body.decode())
            except Exception as e:
                return JsonResponse({'error': f'Invalid JSON payload: {str(e)}'}, status=400)
        else:
            try:
                payload_str = request.POST.get('payload', '{}')
                if not payload_str or payload_str == '{}':
                    return JsonResponse({'error': 'No payload provided in request'}, status=400)
                payload = json.loads(payload_str)
            except Exception as e:
                return JsonResponse({'error': f'Invalid payload: {str(e)}'}, status=400)

        questions = payload.get('questions', [])
        bank_import = payload.get('bank_import')
        deleted_ids = payload.get('deleted_question_ids', [])

        created = []
        updated = []
        deleted = []

        from django.db import transaction

        try:
            with transaction.atomic():
                # delete removed questions
                if deleted_ids:
                    for qid in deleted_ids:
                        qobj = CBTQuestion.objects.filter(pk=qid, exam=exam).first()
                        if qobj:
                            qobj.delete()
                            deleted.append(qid)

                for idx, q in enumerate(questions):
                    existing_id = q.get('existing_id')
                    if existing_id:
                        qobj = CBTQuestion.objects.filter(pk=existing_id, exam=exam).first()
                    else:
                        qobj = None

                    if qobj:
                        qobj.prompt = q.get('prompt', qobj.prompt)
                        qobj.question_type = q.get('question_type', qobj.question_type)
                        qobj.mark_value = q.get('mark_value', qobj.mark_value)
                        qobj.explanation = q.get('explanation', qobj.explanation)
                        qobj.topic = q.get('topic', qobj.topic)
                        qobj.difficulty = q.get('difficulty', qobj.difficulty)
                        qobj.order = q.get('order', qobj.order)
                        qobj.is_active = q.get('is_active', True)
                        qobj.save()
                        updated.append(qobj.id)
                        qobj.choices.all().delete()
                    else:
                        qobj = CBTQuestion.objects.create(
                            exam=exam,
                            question_bank=None,
                            prompt=q.get('prompt', ''),
                            question_type=q.get('question_type', CBTQuestion.MCQ),
                            mark_value=q.get('mark_value', 1.0),
                            explanation=q.get('explanation', ''),
                            topic=q.get('topic', ''),
                            difficulty=q.get('difficulty', CBTQuestion.DIFFICULTY_MEDIUM),
                            order=q.get('order', idx),
                            is_active=q.get('is_active', True)
                        )
                        created.append(qobj.id)

                    if request.FILES:
                        image_key = f'image_{existing_id or qobj.id}'
                        if image_key in request.FILES:
                            qobj.image = request.FILES[image_key]
                            qobj.save()

                    for cidx, ch in enumerate(q.get('choices', [])):
                        CBTChoice.objects.create(
                            question=qobj,
                            text=ch.get('text', ''),
                            is_correct=bool(ch.get('is_correct', False)),
                            order=ch.get('order', cidx)
                        )

                if bank_import:
                    bank_id = bank_import.get('bank_id')
                    selected_ids = bank_import.get('question_ids', [])
                    qb = get_object_or_404(QuestionBank, pk=bank_id, created_by=request.user)
                    for qid in selected_ids:
                        src = get_object_or_404(CBTQuestion, pk=qid, question_bank=qb)
                        nq = CBTQuestion.objects.create(
                            exam=exam,
                            question_bank=qb,
                            prompt=src.prompt,
                            question_type=src.question_type,
                            mark_value=src.mark_value,
                            explanation=src.explanation,
                            topic=src.topic,
                            difficulty=src.difficulty,
                            order=src.order,
                            is_active=src.is_active
                        )
                        for c in src.choices.all():
                            CBTChoice.objects.create(
                                question=nq,
                                text=c.text,
                                is_correct=c.is_correct,
                                order=c.order
                            )
                        created.append(nq.id)

        except Exception as e:
            return JsonResponse({'error': f'Save failed: {str(e)}'}, status=500)

        return JsonResponse({'status': 'ok', 'created': created, 'updated': updated, 'deleted': deleted})
