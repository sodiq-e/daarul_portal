"""
Exam Workflow Views - Simplified Paper Creation with Rich Content

Handles the new exam paper workflow with CKEditor integration, approval workflow,
and export to PDF/DOCX formats.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.generic import View, ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Q
from datetime import datetime
from io import BytesIO

from .models import ExamPaper, ExamSection, Question, ApprovalLog
from .forms import ExamApprovalForm, ExamExportForm
from .export_utils import export_exam_to_docx, export_exam_to_pdf_html
from accounts.models import User


def user_is_teacher(user):
    """Check if user is an approved teacher"""
    try:
        return (
            user.profile.is_approved and
            user.groups.filter(name='Teacher').exists()
        )
    except AttributeError:
        return False


def user_is_admin(user):
    """Check if user is admin or staff"""
    try:
        return (
            user.profile.is_approved and
            (user.is_staff or user.groups.filter(name__in=['Admin', 'Staff']).exists())
        )
    except AttributeError:
        return user.is_staff


class ExamPaperPreviewView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Teacher preview of exam paper - clean layout without styling
    Shows how paper will appear to students
    """
    model = ExamPaper
    template_name = 'exams/exam_paper_preview.html'
    context_object_name = 'exam'
    
    def test_func(self):
        exam = self.get_object()
        return (
            user_is_teacher(self.request.user) and
            exam.teacher == self.request.user
        ) or user_is_admin(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = self.get_object()
        
        # Build sections with questions
        sections_data = []
        for section in exam.sections.all():
            questions_data = []
            for q in section.questions.all():
                questions_data.append({
                    'object': q,
                    'text': q.question_text,
                    'marks': q.marks,
                    'options': q.options.all(),
                })
            
            sections_data.append({
                'object': section,
                'questions': questions_data,
            })
        
        context['sections_data'] = sections_data
        context['can_submit'] = exam.approval_status == 'draft' and exam.teacher == self.request.user
        context['can_approve'] = exam.approval_status == 'pending' and user_is_admin(self.request.user)
        
        return context


class ExamPaperSubmitForApprovalView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Teacher submits exam paper for admin approval
    Changes status from draft → pending
    """
    
    def test_func(self):
        return user_is_teacher(self.request.user)
    
    @method_decorator(require_POST)
    def post(self, request, pk):
        exam = get_object_or_404(ExamPaper, pk=pk, teacher=request.user)
        
        # Validation: must have questions before submission
        if not exam.sections.exists() or not Question.objects.filter(section__exam=exam).exists():
            messages.error(request, 'Exam must have at least one section with questions before submission.')
            return redirect('exam_paper_detail', pk=pk)
        
        # Change status
        exam.approval_status = 'pending'
        exam.submitted_at = timezone.now()
        exam.save()
        
        # Log action
        ApprovalLog.objects.create(
            exam=exam,
            action='submit',
            user=request.user,
            comment='Exam submitted for approval'
        )
        
        messages.success(request, 'Exam paper submitted for approval. Awaiting admin review.')
        return redirect('exam_paper_detail', pk=pk)


class PendingExamApprovalListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Admin dashboard showing pending exam papers awaiting approval
    """
    model = ExamPaper
    template_name = 'exams/exam_approval_list.html'
    context_object_name = 'exams'
    paginate_by = 20
    
    def test_func(self):
        return user_is_admin(self.request.user)
    
    def get_queryset(self):
        return ExamPaper.objects.filter(
            approval_status='pending'
        ).select_related(
            'subject', 'school_class', 'term', 'teacher'
        ).order_by('-submitted_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = {
            'pending_count': ExamPaper.objects.filter(approval_status='pending').count(),
            'approved_count': ExamPaper.objects.filter(approval_status='approved').count(),
            'rejected_count': ExamPaper.objects.filter(approval_status='rejected').count(),
        }
        return context


class ExamApprovalDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Admin review of exam paper pending approval
    Shows complete paper with teacher guide and answers
    """
    model = ExamPaper
    template_name = 'exams/exam_approval_detail.html'
    context_object_name = 'exam'
    
    def test_func(self):
        exam = self.get_object()
        return user_is_admin(self.request.user) and exam.approval_status == 'pending'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = self.get_object()
        
        # Build sections with full question details including teacher guide
        sections_data = []
        for section in exam.sections.all():
            questions_data = []
            for q in section.questions.all():
                questions_data.append({
                    'object': q,
                    'text': q.question_text,
                    'marks': q.marks,
                    'teacher_guide': q.teacher_guide,
                    'answer_explanation': q.answer_explanation,
                    'resource_notes': q.resource_notes,
                    'options': q.options.all(),
                })
            
            sections_data.append({
                'object': section,
                'questions': questions_data,
            })
        
        context['sections_data'] = sections_data
        context['form'] = ExamApprovalForm()
        context['approval_logs'] = exam.approval_logs.all()
        
        return context


class ExamApprovalActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Admin approves, rejects, or requests changes to exam paper
    """
    
    def test_func(self):
        return user_is_admin(self.request.user)
    
    @method_decorator(require_POST)
    def post(self, request, pk):
        exam = get_object_or_404(ExamPaper, pk=pk)
        form = ExamApprovalForm(request.POST)
        
        if not form.is_valid():
            messages.error(request, 'Form validation failed.')
            return redirect('exam_approval_detail', pk=pk)
        
        action = request.POST.get('action')
        notes = form.cleaned_data.get('approval_notes', '')
        
        if action not in ['approve', 'reject', 'return']:
            messages.error(request, 'Invalid action.')
            return redirect('exam_approval_detail', pk=pk)
        
        # Validate that notes are provided for rejections
        if action in ['reject', 'return'] and not notes:
            messages.warning(request, 'It is recommended to provide feedback when rejecting or returning.')
        
        # Update exam status
        if action == 'approve':
            exam.approval_status = 'approved'
            exam.approved_at = timezone.now()
            exam.approved_by = request.user
            exam.approval_notes = notes
            status_display = 'approved'
            action_display = 'Approved'
        elif action == 'reject':
            exam.approval_status = 'rejected'
            exam.approval_notes = notes
            status_display = 'rejected'
            action_display = 'Rejected'
        elif action == 'return':
            exam.approval_status = 'draft'
            exam.approval_notes = notes
            status_display = 'returned for revision'
            action_display = 'Returned for Review'
        
        exam.save()
        
        # Log approval action
        ApprovalLog.objects.create(
            exam=exam,
            action=action,
            user=request.user,
            comment=notes
        )
        
        # Send notification to teacher (if implementing notification system)
        # notify_teacher(exam, action, notes)
        
        messages.success(request, f'Exam paper {status_display}.')
        return redirect('exam_approval_detail', pk=pk)


class ExamPaperExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Admin exports approved exam paper to PDF or DOCX
    """
    
    def test_func(self):
        exam = self.get_object()
        return user_is_admin(self.request.user) and exam.approval_status == 'approved'
    
    def get_object(self):
        return get_object_or_404(ExamPaper, pk=self.kwargs['pk'])
    
    @method_decorator(require_POST)
    def post(self, request, pk):
        exam = self.get_object()
        form = ExamExportForm(request.POST)
        
        if not form.is_valid():
            messages.error(request, 'Invalid export options.')
            return redirect('exam_approval_detail', pk=pk)
        
        export_format = form.cleaned_data['format']
        include_answers = form.cleaned_data['include_answers']
        include_marks = form.cleaned_data['include_marks']
        
        try:
            if export_format == 'docx':
                return self._export_docx(exam, include_answers, include_marks)
            elif export_format == 'pdf':
                return self._export_pdf(exam, include_answers, include_marks)
            else:
                messages.error(request, 'Unsupported format.')
                return redirect('exam_approval_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Export failed: {str(e)}')
            return redirect('exam_approval_detail', pk=pk)
    
    def _export_docx(self, exam, include_answers, include_marks):
        """Export to DOCX format"""
        output = export_exam_to_docx(
            exam,
            include_answers=include_answers,
            include_marks=include_marks
        )
        
        filename = f"{exam.subject.name}_{exam.school_class}_{exam.term}.docx"
        filename = filename.replace(' ', '_').replace('/', '_')
        
        response = FileResponse(
            output,
            as_attachment=True,
            filename=filename,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
        return response
    
    def _export_pdf(self, exam, include_answers, include_marks):
        """Export to PDF format (requires WeasyPrint)"""
        from django.template.loader import render_to_string
        
        # Get context data
        context_data = export_exam_to_pdf_html(
            exam,
            include_answers=include_answers,
            include_marks=include_marks
        )
        
        # Render HTML
        html_string = render_to_string(
            'exams/exam_export_pdf.html',
            context_data
        )
        
        # Try to use WeasyPrint if available
        try:
            from weasyprint import HTML
            pdf = HTML(string=html_string).write_pdf()
            
            filename = f"{exam.subject.name}_{exam.school_class}_{exam.term}.pdf"
            filename = filename.replace(' ', '_').replace('/', '_')
            
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
        except ImportError:
            # Fallback to HTML if WeasyPrint not available
            messages.warning(self.request, 'PDF export not available. Serving HTML instead.')
            response = HttpResponse(html_string, content_type='text/html')
            return response


class ApprovedExamsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Admin list of approved exams ready for export/printing
    """
    model = ExamPaper
    template_name = 'exams/exam_approved_list.html'
    context_object_name = 'exams'
    paginate_by = 20
    
    def test_func(self):
        return user_is_admin(self.request.user)
    
    def get_queryset(self):
        return ExamPaper.objects.filter(
            approval_status='approved'
        ).select_related(
            'subject', 'school_class', 'term', 'teacher', 'approved_by'
        ).order_by('-approved_at')


class ExamApprovalHistoryView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    View approval history and logs for an exam paper
    """
    model = ExamPaper
    template_name = 'exams/exam_approval_history.html'
    context_object_name = 'exam'
    
    def test_func(self):
        exam = self.get_object()
        return (
            user_is_admin(self.request.user) or
            (user_is_teacher(self.request.user) and exam.teacher == self.request.user)
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = self.get_object()
        context['approval_logs'] = exam.approval_logs.all().order_by('-timestamp')
        context['status_display'] = exam.get_approval_status_display()
        return context
