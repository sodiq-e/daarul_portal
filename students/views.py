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
            context['results'] = StudentResult.objects.filter(student=student).select_related('class_subject__subject', 'term').order_by('-term__date_end')
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


# ==================== ADMIN: STUDENT PERMISSIONS ====================

def user_is_admin(user):
    """Check if user is admin/staff"""
    try:
        return user.is_staff or user.groups.filter(name__in=['Admin', 'Staff']).exists()
    except:
        return False


@login_required
def grant_student_permission(request, student_id, permission_code):
    """Admin grants a permission to a student"""
    from .models import StudentPermission
    
    if not user_is_admin(request.user):
        return HttpResponseForbidden('You do not have permission.')
    
    student = get_object_or_404(Student, pk=student_id)
    perm, _ = StudentPermission.objects.get_or_create(
        student=student,
        permission=permission_code
    )
    perm.is_granted = True
    perm.granted_by = request.user
    perm.save()

    perm_display = dict(StudentPermission.PERMISSION_CHOICES).get(permission_code)
    messages.success(
        request,
        f'Permission "{perm_display}" granted to {student.full_name()}.'
    )
    return redirect('student_permissions', student_id=student_id)


@login_required
def revoke_student_permission(request, student_id, permission_code):
    """Admin revokes a permission from a student"""
    from .models import StudentPermission
    
    if not user_is_admin(request.user):
        return HttpResponseForbidden('You do not have permission.')

    student = get_object_or_404(Student, pk=student_id)
    perm, _ = StudentPermission.objects.get_or_create(
        student=student,
        permission=permission_code
    )
    perm.is_granted = False
    perm.save()

    perm_display = dict(StudentPermission.PERMISSION_CHOICES).get(permission_code)
    messages.success(
        request,
        f'Permission "{perm_display}" revoked from {student.full_name()}.'
    )
    return redirect('student_permissions', student_id=student_id)


class StudentPermissionsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Admin manages student permissions"""
    from .models import StudentPermission
    
    template_name = 'students/admin/permissions_list.html'
    context_object_name = 'permissions'
    paginate_by = 50

    def test_func(self):
        return user_is_admin(self.request.user)

    def get_queryset(self):
        from .models import StudentPermission
        student_id = self.kwargs.get('student_id')
        if student_id:
            return StudentPermission.objects.filter(
                student_id=student_id
            ).select_related('student__user', 'granted_by')
        return StudentPermission.objects.select_related(
            'student__user', 'granted_by'
        ).order_by('-granted_at')

    def get_context_data(self, **kwargs):
        from .models import StudentPermission
        context = super().get_context_data(**kwargs)
        
        student_id = self.kwargs.get('student_id')
        if student_id:
            try:
                student = Student.objects.get(pk=student_id)
                context['student'] = student
                context['all_permissions'] = StudentPermission.PERMISSION_CHOICES
            except Student.DoesNotExist:
                pass
        
        context['students'] = Student.objects.filter(
            user__is_active=True
        ).select_related('user', 'student_class').order_by('surname', 'other_names')
        
        return context


class BulkStudentPermissionView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin bulk assign/revoke permissions for students"""
    template_name = 'students/admin/bulk_permissions.html'

    def test_func(self):
        return user_is_admin(self.request.user)

    def get_context_data(self, **kwargs):
        from .models import StudentPermission
        context = super().get_context_data(**kwargs)
        context['students'] = Student.objects.filter(
            user__is_active=True
        ).select_related('user').order_by('surname', 'other_names')
        context['permission_choices'] = StudentPermission.PERMISSION_CHOICES
        
        # If a student is selected, show their current permissions
        student_id = self.request.GET.get('student_id')
        if student_id:
            try:
                student = Student.objects.get(pk=student_id)
                context['selected_student'] = student
                
                # Get all permissions with their current granted status for this student
                from .models import StudentPermission
                granted_perms = StudentPermission.objects.filter(
                    student=student,
                    is_granted=True
                ).values_list('permission', flat=True)
                context['granted_permissions'] = list(granted_perms)
            except Student.DoesNotExist:
                pass
        
        return context

    def post(self, request, *args, **kwargs):
        from .models import StudentPermission
        from django.http import HttpResponseForbidden
        
        student_id = request.POST.get('student_id')
        if not student_id:
            messages.error(request, 'Please select a student.')
            return redirect('bulk_student_permissions')
        
        student = get_object_or_404(Student, pk=student_id)
        
        # Get all selected permissions from the form
        selected_permissions = request.POST.getlist('permissions')
        
        # Grant/Revoke all permissions based on checkbox state
        for code, name in StudentPermission.PERMISSION_CHOICES:
            perm_obj, _ = StudentPermission.objects.get_or_create(
                student=student,
                permission=code
            )
            is_granted = code in selected_permissions
            perm_obj.is_granted = is_granted
            perm_obj.granted_by = request.user
            perm_obj.save()

        messages.success(
            request,
            f'Permissions updated for {student.full_name()}.'
        )
        return redirect('student_permissions', student_id=student_id)
