from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.db.models import Avg
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.utils.decorators import method_decorator
from .models import CBTExam, CBTQuestion, CBTStudentAttempt, CBTAnswer, CBTChoice
from .forms import CBTExamForm, CBTQuestionForm, CBTChoiceFormSet
from .services import create_attempt, grade_attempt, save_answer, build_attempt_context
from django.http import JsonResponse, HttpResponseForbidden
import json


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
    attempt_questions = attempt.attempt_questions.select_related('question').order_by('randomized_position')
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
    context['total_questions'] = attempt.attempt_questions.count() or attempt.exam.questions.filter(is_active=True).count()
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

    question = get_object_or_404(CBTQuestion, pk=question_id)
    # handle multi-select
    if selected_choice_ids is not None:
        save_answer(attempt=attempt, question=question, selected_choice=selected_choice_ids, text_answer='')
    else:
        sel_choice_obj = None
        if selected_choice:
            try:
                sel_choice_obj = CBTChoice.objects.get(pk=int(selected_choice), question=question)
            except Exception:
                sel_choice_obj = None
        save_answer(attempt=attempt, question=question, selected_choice=sel_choice_obj, text_answer=text_answer)

    return JsonResponse({'status': 'saved', 'last_saved': attempt.last_saved_at.isoformat()})


@login_required
def api_submit_attempt(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    try:
        data = json.loads(request.body.decode())
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    attempt_uuid = data.get('attempt_uuid')
    attempt = get_object_or_404(CBTStudentAttempt, uuid=attempt_uuid)
    if attempt.student and attempt.student != request.user:
        return HttpResponseForbidden()
    if attempt.is_submitted:
        return JsonResponse({'error': 'already submitted'}, status=400)

    # grade and finalize
    grade_attempt(attempt)
    return JsonResponse({'status': 'submitted', 'score': float(attempt.score or 0)})


@method_decorator(login_required, name='dispatch')
class StudentCBTDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'cbt/student_dashboard.html'

    def test_func(self):
        return is_cbt_student(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        context['active_attempts'] = CBTStudentAttempt.objects.filter(
            student=self.request.user,
            is_submitted=False
        ).select_related('exam').order_by('-started_at')
        context['recent_cbt_results'] = CBTStudentAttempt.objects.filter(
            student=self.request.user,
            is_submitted=True
        ).select_related('exam').order_by('-completed_at')[:5]
        student_class = getattr(getattr(self.request.user, 'student_profile', None), 'student_class', None)
        if student_class:
            context['upcoming_cbt_exams'] = CBTExam.objects.filter(
                exam_mode=CBTExam.REAL,
                is_active=True,
                is_published=True,
                start_datetime__gt=now,
                school_class=student_class
            ).order_by('start_datetime')
        else:
            context['upcoming_cbt_exams'] = CBTExam.objects.none()
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
        context['attempts'] = CBTStudentAttempt.objects.filter(
            student=self.request.user
        ).select_related('exam').order_by('-started_at')
        return context


@method_decorator(login_required, name='dispatch')
class StudentCBTResultListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'cbt/student_result_list.html'

    def test_func(self):
        return is_cbt_student(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['attempts'] = CBTStudentAttempt.objects.filter(
            student=self.request.user,
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
        ).select_related('exam', 'student').order_by('-started_at')


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
        return context
