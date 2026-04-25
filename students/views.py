from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from .models import Student, StudentApplication, AdmissionFormField, AdmissionFormResponse
from .forms import StudentForm, StudentApplicationForm, StudentApplicationReviewForm, DynamicAdmissionForm


def user_profile_approved(user):
    """Defensively check if user profile is approved"""
    try:
        return user.profile.is_approved
    except AttributeError:
        return False


def staff_can_edit(user):
    """Check if user can edit student records"""
    if not user or not user.is_authenticated:
        return False
    
    try:
        return (
            getattr(user, 'profile', None) is not None and
            user.profile.is_approved and
            user.groups.filter(name__in=['Teacher', 'Staff']).exists()
        )
    except AttributeError:
        return False
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in staff_can_edit: {str(e)}")
        return False


class StudentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 20

    def test_func(self):
        return user_profile_approved(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = staff_can_edit(self.request.user)
        return context


class StudentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'

    def test_func(self):
        return user_profile_approved(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = staff_can_edit(self.request.user)
        return context


class StudentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student_list')

    def test_func(self):
        return staff_can_edit(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Student created successfully.')
        return super().form_valid(form)


class StudentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student_list')

    def test_func(self):
        return staff_can_edit(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Student updated successfully.')
        return super().form_valid(form)


class StudentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Student
    template_name = 'students/student_confirm_delete.html'
    success_url = reverse_lazy('student_list')

    def test_func(self):
        return staff_can_edit(self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Student deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
def student_status_update(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        date_left = request.POST.get('date_left')
        if status in ['transferred', 'graduated']:
            student.status = status
            if date_left:
                student.date_left = date_left
            student.save()
            messages.success(request, f'Student status updated to {status}.')
            return redirect('student_detail', pk=pk)
    return render(request, 'students/student_status_update.html', {'student': student})


class StudentApplicationCreateView(CreateView):
    model = StudentApplication
    form_class = StudentApplicationForm
    template_name = 'students/student_application_modern.html'
    success_url = reverse_lazy('student_application')

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.submitted_by = self.request.user
        messages.success(self.request, '✓ Your application has been submitted successfully. The school will review it shortly.')
        return super().form_valid(form)


class StudentApplicationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = StudentApplication
    template_name = 'students/student_application_list.html'
    context_object_name = 'applications'
    paginate_by = 20

    def test_func(self):
        return staff_can_edit(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = self.get_queryset().filter(status='pending').count()
        context['accepted_count'] = self.get_queryset().filter(status='accepted').count()
        context['rejected_count'] = self.get_queryset().filter(status='rejected').count()
        return context


class StudentApplicationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = StudentApplication
    template_name = 'students/student_application_detail.html'
    context_object_name = 'application'

    def test_func(self):
        return staff_can_edit(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_responses'] = AdmissionFormResponse.objects.filter(
            application=self.object
        ).select_related('field')
        return context


@login_required
def print_admission_application(request, pk):
    """Print admission application in PDF format"""
    if not request.user.is_staff:
        return redirect('home')
    
    application = get_object_or_404(StudentApplication, pk=pk)
    form_responses = AdmissionFormResponse.objects.filter(application=application).select_related('field')
    
    context = {
        'application': application,
        'form_responses': form_responses,
    }
    
    html_string = render_to_string('students/admission_application_print.html', context)
    
    # Try to generate PDF, fallback to HTML if weasyprint not available
    try:
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Application_{application.id}.pdf"'
        return response
    except:
        # Fallback: return HTML for printing
        return HttpResponse(html_string)


class StudentApplicationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = StudentApplication
    form_class = StudentApplicationReviewForm
    template_name = 'students/student_application_form.html'
    success_url = reverse_lazy('student_application_list')

    def test_func(self):
        return staff_can_edit(self.request.user)

    def form_valid(self, form):
        form.instance.reviewed_by = self.request.user
        messages.success(self.request, 'Application updated successfully.')
        return super().form_valid(form)


# ==================== STUDENT PORTAL VIEWS ====================

class StudentDashboardView(LoginRequiredMixin, TemplateView):
    """Student view their own profile and summary"""
    template_name = 'students/portal/student_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            student = self.request.user.student_profile
            context['student'] = student
            context['invoices'] = student.invoices.all().order_by('-issued_date')
            context['pending_invoices'] = student.invoices.filter(status='pending').count()
            context['total_owing'] = sum(inv.balance for inv in student.invoices.filter(status__in=['pending', 'overdue']))
        except Student.DoesNotExist:
            context['student'] = None
        return context
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'student_profile'):
            messages.error(request, 'You do not have a student profile linked to your account.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class StudentProfileDetailView(LoginRequiredMixin, DetailView):
    """Student view their full profile"""
    model = Student
    template_name = 'students/portal/student_profile.html'
    context_object_name = 'student'
    
    def get_object(self):
        return self.request.user.student_profile
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'student_profile'):
            messages.error(request, 'You do not have a student profile.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class StudentResultsView(LoginRequiredMixin, TemplateView):
    """Student view their academic results"""
    template_name = 'students/portal/student_results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from results.models import StudentResult
            student = self.request.user.student_profile
            context['student'] = student
            context['results'] = StudentResult.objects.filter(student=student).select_related('exam', 'subject').order_by('-exam__date')
        except Student.DoesNotExist:
            context['student'] = None
            context['results'] = []
        return context


class StudentFeesView(LoginRequiredMixin, TemplateView):
    """Student view their fee/invoice records"""
    template_name = 'students/portal/student_fees.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from payroll.models import StudentPayment
            student = self.request.user.student_profile
            context['student'] = student
            context['invoices'] = student.invoices.all().order_by('-issued_date')
            context['payments'] = StudentPayment.objects.filter(student=student).order_by('-payment_date')
            
            # Summary calculations
            total_due = sum(inv.amount_due for inv in context['invoices'])
            total_paid = sum(p.amount for p in context['payments'])
            context['total_due'] = total_due
            context['total_paid'] = total_paid
            context['total_owing'] = total_due - total_paid
        except Student.DoesNotExist:
            context['student'] = None
        return context
