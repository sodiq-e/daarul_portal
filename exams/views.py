from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db import models
from django.views.decorators.http import require_POST
import json

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from .models import Subject, Exam, ExamPaper, ExamSection, Question, QuestionOption, ApprovalLog
from .forms import SubjectForm, ExamForm, ExamPaperForm, ExamReviewForm
from school_classes.models import SchoolClasses, ClassTeacher


def user_profile_approved(user):
    """Defensively check if user profile is approved"""
    try:
        return user.profile.is_approved
    except AttributeError:
        return False


def user_is_staff(user):
    """Defensively check if user is staff"""
    try:
        return (
            user.profile.is_approved and
            user.groups.filter(name__in=['Teacher', 'Staff']).exists()
        )
    except AttributeError:
        return False


def user_is_admin(user):
    """Check if user is admin"""
    try:
        return (
            user.profile.is_approved and
            user.is_staff
        )
    except AttributeError:
        return False


@method_decorator(login_required, name='dispatch')
class SelectClassForSubjectsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Teachers/admins select a class to add subjects to"""
    template_name = 'exams/select_class_for_subjects.html'

    def test_func(self):
        return user_is_staff(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get classes based on user role
        if user_is_admin(user):
            # Admins can see all classes
            classes = SchoolClasses.objects.all().order_by('class_name')
        else:
            # Teachers can only see classes they're assigned to
            assigned_class_ids = ClassTeacher.objects.filter(
                teacher=user.teacher_profile,
                is_active=True
            ).values_list('school_class_id', flat=True).distinct()
            classes = SchoolClasses.objects.filter(id__in=assigned_class_ids).order_by('class_name')
        
        context['classes'] = classes
        return context

    def post(self, request, *args, **kwargs):
        class_id = request.POST.get('school_class')
        
        if class_id:
            return redirect('school_classes:class_subjects_list', class_id=class_id)
        else:
            messages.error(request, 'Please select a class.')
            return redirect('select_class_for_subjects')


# Subject Views
class SubjectListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Subject
    template_name = 'exams/subject_list.html'
    context_object_name = 'subjects'
    paginate_by = 20
    ordering = ['name']

    def test_func(self):
        return user_profile_approved(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = user_is_staff(self.request.user)
        return context


class SubjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Subject
    template_name = 'exams/subject_detail.html'
    context_object_name = 'subject'

    def test_func(self):
        return user_profile_approved(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = user_is_staff(self.request.user)
        return context


class SubjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'exams/subject_form.html'
    success_url = reverse_lazy('subject_list')

    def test_func(self):
        return user_is_staff(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Subject created successfully.')
        return super().form_valid(form)


class SubjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'exams/subject_form.html'
    success_url = reverse_lazy('subject_list')

    def test_func(self):
        return user_is_staff(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Subject updated successfully.')
        return super().form_valid(form)


class SubjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Subject
    template_name = 'exams/subject_confirm_delete.html'
    success_url = reverse_lazy('subject_list')

    def test_func(self):
        return user_is_staff(self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Subject deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Exam Views
class ExamListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Exam
    template_name = 'exams/exam_list.html'
    context_object_name = 'exams'
    paginate_by = 20

    def test_func(self):
        return user_profile_approved(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = user_is_staff(self.request.user)
        return context


class ExamDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Exam
    template_name = 'exams/exam_detail.html'
    context_object_name = 'exam'

    def test_func(self):
        return user_profile_approved(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = user_is_staff(self.request.user)
        return context


class ExamCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'
    success_url = reverse_lazy('exam_list')

    def test_func(self):
        return user_is_staff(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Exam created successfully.')
        return super().form_valid(form)


class ExamUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'
    success_url = reverse_lazy('exam_list')

    def test_func(self):
        return user_is_staff(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Exam updated successfully.')
        return super().form_valid(form)


class ExamDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Exam
    template_name = 'exams/exam_confirm_delete.html'
    success_url = reverse_lazy('exam_list')

    def test_func(self):
        return user_is_staff(self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Exam deleted successfully.')
        return super().delete(request, *args, **kwargs)


class TeacherExamPaperListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ExamPaper
    template_name = 'exams/teacher_exam_list.html'
    context_object_name = 'exam_papers'
    paginate_by = 20

    def test_func(self):
        return user_profile_approved(self.request.user) and hasattr(self.request.user, 'teacher_profile')

    def get_queryset(self):
        if hasattr(self.request.user, 'teacher_profile'):
            return ExamPaper.objects.filter(teacher=self.request.user.teacher_profile).order_by('-updated_at')
        return ExamPaper.objects.none()


class TeacherExamPaperDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = ExamPaper
    template_name = 'exams/teacher_exam_detail.html'
    context_object_name = 'exam_paper'

    def test_func(self):
        return user_profile_approved(self.request.user) and hasattr(self.request.user, 'teacher_profile')

    def get_queryset(self):
        if hasattr(self.request.user, 'teacher_profile'):
            return ExamPaper.objects.filter(teacher=self.request.user.teacher_profile)
        return ExamPaper.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam_paper = self.get_object()
        context['can_edit'] = exam_paper.status in ['draft', 'returned']
        return context


class TeacherExamPaperCreateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'exams/teacher_exam_form.html'

    def test_func(self):
        return user_profile_approved(self.request.user) and hasattr(self.request.user, 'teacher_profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ExamPaperForm(teacher=self.request.user.teacher_profile)
        context['exam_json'] = json.dumps({})
        context['page_title'] = 'Create Exam Paper'
        context['save_draft_url'] = reverse_lazy('exam_paper_save')
        context['submit_url'] = reverse_lazy('exam_paper_submit')
        return context


class TeacherExamPaperEditView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'exams/teacher_exam_form.html'

    def test_func(self):
        return user_profile_approved(self.request.user) and hasattr(self.request.user, 'teacher_profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam_paper = get_object_or_404(
            ExamPaper,
            pk=kwargs.get('pk'),
            teacher=self.request.user.teacher_profile
        )

        context['form'] = ExamPaperForm(instance=exam_paper, teacher=self.request.user.teacher_profile)
        context['exam_json'] = json.dumps(self._exam_to_payload(exam_paper))
        context['page_title'] = 'Edit Exam Paper'
        context['save_draft_url'] = reverse_lazy('exam_paper_save')
        context['submit_url'] = reverse_lazy('exam_paper_submit')
        context['exam_paper'] = exam_paper
        return context

    def _exam_to_payload(self, exam_paper):
        return {
            'id': exam_paper.id,
            'subject': exam_paper.subject_id,
            'school_class': exam_paper.school_class_id,
            'term': exam_paper.term_id,
            'academic_session': exam_paper.academic_session,
            'duration': exam_paper.duration,
            'total_marks': exam_paper.total_marks,
            'instructions': exam_paper.instructions,
            'sections': [
                {
                    'id': section.id,
                    'title': section.title,
                    'section_type': section.section_type,
                    'instruction': section.instruction,
                    'marks_allocation': section.marks_allocation,
                    'order': section.order,
                    'questions': [
                        {
                            'id': question.id,
                            'question_text': question.question_text,
                            'marks': str(question.marks) if question.marks is not None else '',
                            'order': question.order,
                            'question_type': question.question_type,
                            'correct_answer': question.correct_answer,
                            'teacher_guide': question.teacher_guide,
                            'subnumbering_style': question.subnumbering_style,
                            'options': [
                                {
                                    'id': option.id,
                                    'option_label': option.option_label,
                                    'option_text': option.option_text,
                                }
                                for option in question.options.all()
                            ]
                        }
                        for question in section.questions.all()
                    ]
                }
                for section in exam_paper.sections.all()
            ]
        }


class AdminExamPaperListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ExamPaper
    template_name = 'exams/admin_exam_list.html'
    context_object_name = 'exam_papers'
    paginate_by = 25

    def test_func(self):
        return user_is_admin(self.request.user)

    def get_queryset(self):
        queryset = ExamPaper.objects.all().select_related('subject', 'school_class', 'term', 'teacher')
        status = self.request.GET.get('status')
        query = self.request.GET.get('q')
        if status:
            queryset = queryset.filter(status=status)
        if query:
            queryset = queryset.filter(
                models.Q(subject__name__icontains=query) |
                models.Q(school_class__class_name__icontains=query) |
                models.Q(term__academic_year__icontains=query) |
                models.Q(academic_session__icontains=query) |
                models.Q(teacher__user__first_name__icontains=query) |
                models.Q(teacher__user__last_name__icontains=query) |
                models.Q(teacher__user__username__icontains=query)
            )
        return queryset.order_by('-submitted_at', '-updated_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['query'] = self.request.GET.get('q', '')
        return context


class AdminExamPaperDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = ExamPaper
    template_name = 'exams/admin_exam_detail.html'
    context_object_name = 'exam_paper'

    def test_func(self):
        return user_is_admin(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['review_form'] = ExamReviewForm()
        context['approval_logs'] = self.object.approval_logs.all()
        return context


class ExamPaperPrintView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return (
            user_is_admin(self.request.user) or
            (hasattr(self.request.user, 'teacher_profile') and
             ExamPaper.objects.filter(pk=self.kwargs.get('pk'), teacher=self.request.user.teacher_profile).exists())
        )

    def get(self, request, pk, *args, **kwargs):
        exam_paper = get_object_or_404(ExamPaper, pk=pk)
        if exam_paper.status != 'approved' and not user_is_admin(request.user):
            return HttpResponse('Only approved exam papers can be printed.', status=403)

        context = {'exam_paper': exam_paper}
        html_string = render_to_string('exams/print_exam_paper.html', context)

        if request.GET.get('format') == 'pdf' and WEASYPRINT_AVAILABLE:
            html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
            pdf = html.write_pdf(stylesheets=[])
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="ExamPaper_{exam_paper.id}.pdf"'
            return response

        return HttpResponse(html_string)


@method_decorator([login_required, require_POST], name='dispatch')
class AdminExamPaperActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return user_is_admin(self.request.user)

    def post(self, request, pk, *args, **kwargs):
        exam_paper = get_object_or_404(ExamPaper, pk=pk)
        form = ExamReviewForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Please enter valid review comments.')
            return redirect('admin_exam_paper_detail', pk=pk)

        action = request.POST.get('action')
        comment = form.cleaned_data['comment']
        if action not in ['approve', 'reject', 'return']:
            messages.error(request, 'Invalid action.')
            return redirect('admin_exam_paper_detail', pk=pk)

        if action in ['reject', 'return'] and not comment:
            messages.error(request, 'Comment is required for rejection or return.')
            return redirect('admin_exam_paper_detail', pk=pk)

        if action == 'approve':
            exam_paper.status = 'approved'
            exam_paper.approved_at = timezone.now()
            messages.success(request, 'Exam paper approved successfully.')
        elif action == 'reject':
            exam_paper.status = 'rejected'
            messages.success(request, 'Exam paper rejected.')
        elif action == 'return':
            exam_paper.status = 'returned'
            messages.success(request, 'Exam paper returned for correction.')

        exam_paper.save()
        ApprovalLog.objects.create(
            exam=exam_paper,
            action=action,
            user=request.user,
            comment=comment
        )

        return redirect('admin_exam_paper_detail', pk=pk)


@method_decorator([login_required, require_POST], name='dispatch')
class ExamPaperSaveView(View):
    def post(self, request, *args, **kwargs):
        payload = self._parse_json(request)
        if payload is None:
            return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

        if not hasattr(request.user, 'teacher_profile'):
            return JsonResponse({'error': 'Teacher profile is required.'}, status=403)

        exam_paper = None
        if payload.get('id'):
            exam_paper = ExamPaper.objects.filter(
                pk=payload.get('id'),
                teacher=request.user.teacher_profile
            ).first()
            if not exam_paper:
                return JsonResponse({'error': 'Exam paper not found.'}, status=404)
            if exam_paper.status == 'approved':
                return JsonResponse({'error': 'Approved exams cannot be edited.'}, status=403)

        form = ExamPaperForm(payload, teacher=request.user.teacher_profile, instance=exam_paper)
        if not form.is_valid():
            return JsonResponse({'errors': form.errors}, status=400)

        exam_paper = form.save(commit=False)
        exam_paper.teacher = request.user.teacher_profile
        exam_paper.status = 'draft'
        exam_paper.save()
        self._save_sections(exam_paper, payload.get('sections', []))

        return JsonResponse({
            'exam_paper_id': exam_paper.id,
            'status': exam_paper.status,
            'saved_at': timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
        })

    def _parse_json(self, request):
        try:
            return json.loads(request.body.decode('utf-8'))
        except (TypeError, ValueError):
            return None

    def _save_sections(self, exam_paper, sections_payload):
        exam_paper.sections.all().delete()
        for index, section_data in enumerate(sections_payload, start=1):
            section = ExamSection.objects.create(
                exam=exam_paper,
                title=section_data.get('title', '').strip(),
                section_type=section_data.get('section_type', 'theory'),
                instruction=section_data.get('instruction', '').strip(),
                marks_allocation=section_data.get('marks_allocation') or 0,
                order=index
            )
            for q_index, question_data in enumerate(section_data.get('questions', []), start=1):
                question = Question.objects.create(
                    section=section,
                    question_text=question_data.get('question_text', '').strip(),
                    marks=question_data.get('marks') or None,
                    order=q_index,
                    question_type=question_data.get('question_type', 'theory'),
                    correct_answer=question_data.get('correct_answer', '').strip(),
                    teacher_guide=question_data.get('teacher_guide', '').strip(),
                    subnumbering_style=question_data.get('subnumbering_style', 'parent_alpha')
                )
                for option in question_data.get('options', []):
                    if option.get('option_label'):
                        QuestionOption.objects.create(
                            question=question,
                            option_label=option.get('option_label'),
                            option_text=option.get('option_text', '').strip()
                        )


@method_decorator([login_required, require_POST], name='dispatch')
class ExamPaperSubmitView(View):
    def post(self, request, *args, **kwargs):
        payload = self._parse_json(request)
        if payload is None:
            return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

        if not hasattr(request.user, 'teacher_profile'):
            return JsonResponse({'error': 'Teacher profile is required.'}, status=403)

        save_view = ExamPaperSaveView()
        save_view.request = request
        save_view.args = args
        save_view.kwargs = kwargs
        save_view._parse_json = ExamPaperSaveView._parse_json
        save_view._save_sections = ExamPaperSaveView._save_sections

        result = save_view.post(request, *args, **kwargs)
        if result.status_code != 200:
            return result

        exam_paper_id = json.loads(result.content.decode('utf-8')).get('exam_paper_id')
        exam_paper = ExamPaper.objects.get(pk=exam_paper_id)
        exam_paper.status = 'submitted'
        exam_paper.submitted_at = timezone.now()
        exam_paper.save()
        ApprovalLog.objects.create(
            exam=exam_paper,
            action='submit',
            user=request.user,
            comment='Submitted for approval.'
        )
        return JsonResponse({'exam_paper_id': exam_paper.id, 'status': exam_paper.status})

    def _parse_json(self, request):
        try:
            return json.loads(request.body.decode('utf-8'))
        except (TypeError, ValueError):
            return None
