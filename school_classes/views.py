from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.utils import timezone
from django.http import HttpResponseForbidden
from .models import (
    SchoolClasses, Teacher, ClassTeacher, SchemeOfWork, SchemeWeek, TeacherPermission
)
from .forms import (
    TeacherProfileForm, TeacherApplicationForm, ClassTeacherForm,
    SchemeOfWorkForm, SchemeWeekForm, TeacherPermissionForm,
    BulkTeacherPermissionForm
)
from exams.models import Subject, ClassSubject
from exams.forms import ClassSubjectForm
from students.models import Student


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


def teacher_has_permission(teacher, permission_code):
    """Check if teacher has specific permission"""
    try:
        perm = TeacherPermission.objects.filter(
            teacher=teacher,
            permission=permission_code,
            is_granted=True
        ).exists()
        return perm
    except:
        return False


@method_decorator(login_required, name='dispatch')
class ClassListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = SchoolClasses
    template_name = 'classes/class_list.html'
    context_object_name = 'classes'

    def test_func(self):
        return user_profile_approved(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = user_is_staff(self.request.user)
        return context


@login_required
def add_class(request):
    if not user_is_staff(request.user):
        messages.error(request, 'You do not have permission to add classes.')
        return redirect('school_classes:class_list')

    if request.method == 'POST':
        name = request.POST.get('class_name')
        level = request.POST.get('level')
        desc = request.POST.get('description')

        # Prevent empty class name
        if name:
            try:
                SchoolClasses.objects.create(
                    class_name=name,
                    level=level,
                    description=desc
                )
            except:
                # Handles duplicate class_name (unique=True)
                pass

        return redirect('school_classes:class_list')

    return render(request, 'classes/add_class.html')


@method_decorator(login_required, name='dispatch')
class ClassDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View students in a specific class"""
    model = SchoolClasses
    template_name = 'classes/class_detail.html'
    context_object_name = 'school_class'

    def test_func(self):
        return user_profile_approved(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school_class = self.get_object()
        context['students'] = Student.objects.filter(
            student_class=school_class,
            status='active'
        ).order_by('surname', 'other_names')
        context['can_modify'] = user_is_staff(self.request.user)
        context['teachers'] = ClassTeacher.objects.filter(
            school_class=school_class,
            is_active=True
        ).select_related('teacher__user', 'subject')
        return context


# ==================== CLASS SUBJECT MANAGEMENT ====================

@login_required
def class_subjects_list(request, class_id):
    """List and manage subjects for a class"""
    if not user_is_admin(request.user):
        messages.error(request, 'You do not have permission to manage class subjects.')
        return redirect('home')
    
    school_class = get_object_or_404(SchoolClasses, pk=class_id)
    subjects = ClassSubject.objects.filter(school_class=school_class).select_related('subject').order_by('order')
    available_subjects = Subject.objects.exclude(
        pk__in=subjects.values_list('subject_id', flat=True)
    ).filter(is_active=True)
    
    context = {
        'school_class': school_class,
        'subjects': subjects,
        'available_subjects': available_subjects,
    }
    return render(request, 'classes/class_subjects_list.html', context)


@login_required
def add_class_subject(request, class_id):
    """Add a subject to a class"""
    if not user_is_admin(request.user):
        messages.error(request, 'You do not have permission to manage class subjects.')
        return redirect('home')
    
    school_class = get_object_or_404(SchoolClasses, pk=class_id)
    
    if request.method == 'POST':
        form = ClassSubjectForm(request.POST)
        if form.is_valid():
            class_subject = form.save(commit=False)
            class_subject.school_class = school_class
            try:
                class_subject.save()
                messages.success(request, f'{class_subject.subject.name} added to {school_class.class_name} successfully.')
                return redirect('class_subjects_list', class_id=class_id)
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = ClassSubjectForm()
        # Filter to only show subjects not already assigned to this class
        existing = ClassSubject.objects.filter(school_class=school_class).values_list('subject_id', flat=True)
        form.fields['subject'].queryset = Subject.objects.exclude(pk__in=existing).filter(is_active=True)
        form.fields['school_class'].initial = school_class
        form.fields['school_class'].disabled = True
    
    context = {
        'form': form,
        'school_class': school_class,
        'action': 'Add',
    }
    return render(request, 'classes/class_subject_form.html', context)


@login_required
def edit_class_subject(request, subject_id):
    """Edit a class subject"""
    if not user_is_admin(request.user):
        messages.error(request, 'You do not have permission to manage class subjects.')
        return redirect('home')
    
    class_subject = get_object_or_404(ClassSubject, pk=subject_id)
    
    if request.method == 'POST':
        form = ClassSubjectForm(request.POST, instance=class_subject)
        if form.is_valid():
            form.save()
            messages.success(request, f'{class_subject.subject.name} updated successfully.')
            return redirect('class_subjects_list', class_id=class_subject.school_class.id)
    else:
        form = ClassSubjectForm(instance=class_subject)
        form.fields['school_class'].disabled = True
        form.fields['subject'].disabled = True
    
    context = {
        'form': form,
        'school_class': class_subject.school_class,
        'class_subject': class_subject,
        'action': 'Edit',
    }
    return render(request, 'classes/class_subject_form.html', context)


@login_required
def delete_class_subject(request, subject_id):
    """Delete a subject from a class"""
    if not user_is_admin(request.user):
        messages.error(request, 'You do not have permission to manage class subjects.')
        return redirect('home')
    
    class_subject = get_object_or_404(ClassSubject, pk=subject_id)
    class_id = class_subject.school_class.id
    subject_name = class_subject.subject.name
    class_name = class_subject.school_class.class_name
    
    class_subject.delete()
    messages.success(request, f'{subject_name} removed from {class_name}.')
    return redirect('class_subjects_list', class_id=class_id)


# ==================== TEACHER PROFILE VIEWS ====================

@login_required
def teacher_dashboard(request):
    """Teacher dashboard - redirects based on user role"""
    if user_is_admin(request.user):
        return redirect('teachers:teacher_list')
    elif user_is_staff(request.user):
        try:
            teacher = request.user.teacher_profile
            if teacher.is_approved:
                return redirect('teachers:teacher_profile')
        except:
            pass
    return redirect('teachers:teacher_apply')


class TeacherApplicationView(CreateView):
    """Teachers can apply for registration"""
    form_class = TeacherApplicationForm
    template_name = 'teachers/teacher_application.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        messages.success(
            self.request,
            'Application submitted successfully. Awaiting admin approval.'
        )
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class TeacherProfileView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Teacher's own profile view"""
    model = Teacher
    template_name = 'teachers/teacher_profile.html'
    context_object_name = 'teacher'

    def test_func(self):
        return user_profile_approved(self.request.user)

    def get_object(self):
        try:
            return self.request.user.teacher_profile
        except Teacher.DoesNotExist:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.get_object():
            context['assigned_classes'] = ClassTeacher.objects.filter(
                teacher=self.get_object(),
                is_active=True
            ).select_related('school_class', 'subject')
            context['schemes'] = SchemeOfWork.objects.filter(
                teacher=self.get_object()
            ).order_by('-created_at')
        return context


@method_decorator(login_required, name='dispatch')
class TeacherProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Teachers can edit their profile"""
    model = Teacher
    form_class = TeacherProfileForm
    template_name = 'teachers/teacher_profile_edit.html'
    success_url = reverse_lazy('teacher_profile')

    def test_func(self):
        try:
            teacher = self.get_object()
            return self.request.user.teacher_profile == teacher
        except:
            return False

    def get_object(self):
        try:
            return self.request.user.teacher_profile
        except Teacher.DoesNotExist:
            return None

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)


# ==================== ADMIN: TEACHER MANAGEMENT VIEWS ====================

@method_decorator(login_required, name='dispatch')
class TeacherListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Admin view to list all teachers"""
    model = Teacher
    template_name = 'teachers/admin/teacher_list.html'
    context_object_name = 'teachers'
    paginate_by = 20

    def test_func(self):
        return user_is_admin(self.request.user)

    def get_queryset(self):
        queryset = Teacher.objects.all().select_related('user', 'approved_by')
        
        # Filter by approval status if specified
        status = self.request.GET.get('status')
        if status == 'approved':
            queryset = queryset.filter(is_approved=True)
        elif status == 'pending':
            queryset = queryset.filter(is_approved=False)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-date_joined')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = Teacher.objects.filter(is_approved=False).count()
        context['approved_count'] = Teacher.objects.filter(is_approved=True).count()
        context['current_status'] = self.request.GET.get('status', 'all')
        return context


@method_decorator(login_required, name='dispatch')
class TeacherDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Admin view of teacher details"""
    model = Teacher
    template_name = 'teachers/admin/teacher_detail.html'
    context_object_name = 'teacher'

    def test_func(self):
        return user_is_admin(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.get_object()
        context['assigned_classes'] = ClassTeacher.objects.filter(
            teacher=teacher
        ).select_related('school_class', 'subject')
        context['permissions'] = TeacherPermission.objects.filter(
            teacher=teacher
        )
        context['schemes'] = SchemeOfWork.objects.filter(
            teacher=teacher
        ).order_by('-created_at')
        return context


@login_required
def approve_teacher(request, pk):
    """Admin approves a teacher"""
    if not user_is_admin(request.user):
        messages.error(request, 'You do not have permission to approve teachers.')
        return redirect('teacher_list')

    teacher = get_object_or_404(Teacher, pk=pk)
    teacher.is_approved = True
    teacher.approved_at = timezone.now()
    teacher.approved_by = request.user
    teacher.user.is_active = True
    teacher.user.save()
    teacher.save()

    # Add to Teacher group
    from django.contrib.auth.models import Group
    group, _ = Group.objects.get_or_create(name='Teacher')
    teacher.user.groups.add(group)

    # Initialize all permissions for teacher (all set to False by default)
    for perm_code, perm_name in TeacherPermission.PERMISSION_CHOICES:
        TeacherPermission.objects.get_or_create(
            teacher=teacher,
            permission=perm_code,
            defaults={'is_granted': False}
        )

    messages.success(request, f'{teacher.user.get_full_name()} has been approved.')
    return redirect('teachers:teacher_detail', pk=pk)


@login_required
def reject_teacher(request, pk):
    """Admin rejects a teacher application"""
    if not user_is_admin(request.user):
        messages.error(request, 'You do not have permission to reject teachers.')
        return redirect('teacher_list')

    teacher = get_object_or_404(Teacher, pk=pk)
    teacher.is_active = False
    teacher.user.is_active = False
    teacher.user.save()
    teacher.save()

    messages.success(request, f'{teacher.user.get_full_name()} has been rejected.')
    return redirect('teacher_list')


# ==================== ADMIN: CLASS TEACHER ASSIGNMENT ====================

@method_decorator(login_required, name='dispatch')
class ClassTeacherListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Admin view of teacher-class assignments"""
    model = ClassTeacher
    template_name = 'teachers/admin/class_teacher_list.html'
    context_object_name = 'assignments'
    paginate_by = 30

    def test_func(self):
        return user_is_admin(self.request.user)

    def get_queryset(self):
        return ClassTeacher.objects.filter(is_active=True).select_related(
            'teacher__user', 'school_class', 'subject'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classes'] = SchoolClasses.objects.all()
        return context


@method_decorator(login_required, name='dispatch')
class ClassTeacherCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Admin assigns teacher to class"""
    model = ClassTeacher
    form_class = ClassTeacherForm
    template_name = 'teachers/admin/class_teacher_form.html'
    success_url = reverse_lazy('class_teacher_list')

    def test_func(self):
        return user_is_admin(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Only show approved teachers
        if self.request.method == 'GET':
            kwargs['queryset'] = Teacher.objects.filter(is_approved=True)
        return kwargs

    def form_valid(self, form):
        messages.success(
            self.request,
            f'{form.instance.teacher} assigned to {form.instance.school_class} - {form.instance.subject}'
        )
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class ClassTeacherUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Admin updates teacher assignment"""
    model = ClassTeacher
    form_class = ClassTeacherForm
    template_name = 'teachers/admin/class_teacher_form.html'
    success_url = reverse_lazy('class_teacher_list')

    def test_func(self):
        return user_is_admin(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Assignment updated successfully.')
        return super().form_valid(form)


@login_required
def deactivate_class_teacher(request, pk):
    """Admin deactivates a teacher-class assignment"""
    if not user_is_admin(request.user):
        return HttpResponseForbidden('You do not have permission.')

    assignment = get_object_or_404(ClassTeacher, pk=pk)
    assignment.is_active = False
    assignment.save()
    messages.success(request, 'Assignment deactivated.')
    return redirect('class_teacher_list')


# ==================== ADMIN: TEACHER PERMISSIONS ====================

@method_decorator(login_required, name='dispatch')
class TeacherPermissionsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Admin manages teacher permissions"""
    model = TeacherPermission
    template_name = 'teachers/admin/permissions_list.html'
    context_object_name = 'permissions'
    paginate_by = 50

    def test_func(self):
        return user_is_admin(self.request.user)

    def get_queryset(self):
        teacher_id = self.kwargs.get('teacher_id')
        if teacher_id:
            return TeacherPermission.objects.filter(
                teacher_id=teacher_id
            ).select_related('teacher__user').order_by('teacher__user__last_name', 'permission')
        return TeacherPermission.objects.all().select_related('teacher__user').order_by('teacher__user__last_name', 'permission')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher_id = self.kwargs.get('teacher_id')
        if teacher_id:
            context['teacher'] = get_object_or_404(Teacher, pk=teacher_id)
            context['permission_choices'] = TeacherPermission.PERMISSION_CHOICES
        return context


@login_required
def grant_teacher_permission(request, teacher_id, permission_code):
    """Admin grants specific permission to teacher"""
    if not user_is_admin(request.user):
        return HttpResponseForbidden('You do not have permission.')

    teacher = get_object_or_404(Teacher, pk=teacher_id)
    perm, created = TeacherPermission.objects.get_or_create(
        teacher=teacher,
        permission=permission_code
    )
    perm.is_granted = True
    perm.granted_by = request.user
    perm.granted_at = timezone.now()
    perm.save()

    perm_display = dict(TeacherPermission.PERMISSION_CHOICES).get(permission_code)
    messages.success(
        request,
        f'Permission "{perm_display}" granted to {teacher.user.get_full_name()}.'
    )
    return redirect('teacher_permissions', teacher_id=teacher_id)


@login_required
def revoke_teacher_permission(request, teacher_id, permission_code):
    """Admin revokes specific permission from teacher"""
    if not user_is_admin(request.user):
        return HttpResponseForbidden('You do not have permission.')

    teacher = get_object_or_404(Teacher, pk=teacher_id)
    perm, created = TeacherPermission.objects.get_or_create(
        teacher=teacher,
        permission=permission_code
    )
    perm.is_granted = False
    perm.save()

    perm_display = dict(TeacherPermission.PERMISSION_CHOICES).get(permission_code)
    messages.success(
        request,
        f'Permission "{perm_display}" revoked from {teacher.user.get_full_name()}.'
    )
    return redirect('teacher_permissions', teacher_id=teacher_id)


@method_decorator(login_required, name='dispatch')
class BulkPermissionView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin bulk assign/revoke permissions for a teacher"""
    template_name = 'teachers/admin/bulk_permissions.html'

    def test_func(self):
        return user_is_admin(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teachers'] = Teacher.objects.filter(is_approved=True).select_related('user').order_by('user__last_name')
        context['permission_choices'] = TeacherPermission.PERMISSION_CHOICES
        
        # If a teacher is selected, show their current permissions
        teacher_id = self.request.GET.get('teacher_id')
        if teacher_id:
            try:
                teacher = Teacher.objects.get(pk=teacher_id)
                context['selected_teacher'] = teacher
                
                # Get all permissions with their current granted status for this teacher
                granted_perms = TeacherPermission.objects.filter(
                    teacher=teacher,
                    is_granted=True
                ).values_list('permission', flat=True)
                context['granted_permissions'] = list(granted_perms)
            except Teacher.DoesNotExist:
                pass
        
        return context

    def post(self, request, *args, **kwargs):
        teacher_id = request.POST.get('teacher_id')
        if not teacher_id:
            messages.error(request, 'Please select a teacher.')
            return redirect('bulk_permissions')
        
        teacher = get_object_or_404(Teacher, pk=teacher_id)
        
        # Get all selected permissions from the form
        selected_permissions = request.POST.getlist('permissions')
        
        # Grant/Revoke all permissions based on checkbox state
        for code, name in TeacherPermission.PERMISSION_CHOICES:
            perm_obj, _ = TeacherPermission.objects.get_or_create(
                teacher=teacher,
                permission=code
            )
            is_granted = code in selected_permissions
            perm_obj.is_granted = is_granted
            perm_obj.granted_by = request.user
            perm_obj.granted_at = timezone.now()
            perm_obj.save()
        
        messages.success(
            request,
            f'Permissions updated for {teacher.user.get_full_name()}.'
        )
        return redirect(f"{reverse('bulk_permissions')}?teacher_id={teacher_id}")


# ==================== TEACHER: SCHEME OF WORK ====================

@method_decorator(login_required, name='dispatch')
class TeacherSchemeListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Teachers view their schemes of work"""
    model = SchemeOfWork
    template_name = 'teachers/scheme/teacher_scheme_list.html'
    context_object_name = 'schemes'
    paginate_by = 20

    def test_func(self):
        try:
            teacher = self.request.user.teacher_profile
            return teacher_has_permission(teacher, 'create_scheme')
        except:
            return False

    def get_queryset(self):
        teacher = self.request.user.teacher_profile
        return SchemeOfWork.objects.filter(teacher=teacher).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get classes where teacher is class teacher (for quick scheme creation)
        teacher = self.request.user.teacher_profile
        context['class_teacher_classes'] = ClassTeacher.objects.filter(
            teacher=teacher,
            is_active=True,
            is_class_teacher=True
        ).select_related('school_class').values_list('school_class', flat=True).distinct()
        return context


@method_decorator(login_required, name='dispatch')
class TeacherSchemeSelectClassView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Teachers select a class before creating a scheme"""
    template_name = 'teachers/scheme/select_class.html'

    def test_func(self):
        try:
            teacher = self.request.user.teacher_profile
            return teacher_has_permission(teacher, 'create_scheme')
        except:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.request.user.teacher_profile
        
        # Get classes where this teacher is assigned
        assigned_classes = ClassTeacher.objects.filter(
            teacher=teacher,
            is_active=True
        ).select_related('school_class').values_list('school_class_id', 'school_class').distinct()
        
        context['assigned_classes'] = [{'id': cls_id, 'name': cls_name} for cls_id, cls_name in assigned_classes]
        context['terms'] = __import__('exams.models', fromlist=['Term']).Term.objects.filter(is_active=True)
        
        return context

    def post(self, request, *args, **kwargs):
        class_id = request.POST.get('school_class')
        term_id = request.POST.get('term')
        
        if class_id and term_id:
            return redirect('teachers:teacher_scheme_create_with_class', class_id=class_id, term_id=term_id)
        else:
            messages.error(request, 'Please select both class and term.')
            return redirect('teachers:teacher_scheme_select_class')


@method_decorator(login_required, name='dispatch')
class TeacherSchemeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Teachers create a new scheme of work"""
    model = SchemeOfWork
    form_class = SchemeOfWorkForm
    template_name = 'teachers/scheme/scheme_form.html'
    success_url = reverse_lazy('teacher_scheme_list')

    def test_func(self):
        try:
            teacher = self.request.user.teacher_profile
            return teacher_has_permission(teacher, 'create_scheme')
        except:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.request.user.teacher_profile
        
        # Get class and term from URL parameters
        class_id = self.kwargs.get('class_id')
        term_id = self.kwargs.get('term_id')
        
        if class_id:
            try:
                school_class = SchoolClasses.objects.get(pk=class_id)
                context['selected_class'] = school_class
                
                # Get subjects offered by this class
                from exams.models import ClassSubject
                class_subjects = ClassSubject.objects.filter(
                    school_class=school_class
                ).select_related('subject')
                context['class_subjects'] = class_subjects
                
            except SchoolClasses.DoesNotExist:
                pass
        
        if term_id:
            try:
                from exams.models import Term
                term = Term.objects.get(pk=term_id)
                context['selected_term'] = term
            except:
                pass
        
        # Get all active terms as fallback
        from exams.models import Term
        context['terms'] = Term.objects.filter(is_active=True)
        
        return context

    def form_valid(self, form):
        form.instance.teacher = self.request.user.teacher_profile
        
        # Get form data for class, subject, and term
        class_id = self.request.POST.get('school_class') or self.kwargs.get('class_id')
        subject_id = self.request.POST.get('subject')
        term_id = self.request.POST.get('term') or self.kwargs.get('term_id')
        
        if class_id and subject_id and term_id:
            form.instance.school_class_id = class_id
            form.instance.subject_id = subject_id
            form.instance.term_id = term_id
            messages.success(self.request, 'Scheme of work created. Now add weekly details.')
            return super().form_valid(form)
        else:
            messages.error(self.request, 'Please select class, subject, and term.')
            return self.form_invalid(form)


@method_decorator(login_required, name='dispatch')
class TeacherSchemeDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View a scheme of work with all weeks"""
    model = SchemeOfWork
    template_name = 'teachers/scheme/scheme_detail.html'
    context_object_name = 'scheme'

    def test_func(self):
        try:
            teacher = self.request.user.teacher_profile
            scheme = self.get_object()
            return scheme.teacher == teacher and teacher_has_permission(teacher, 'edit_scheme')
        except:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scheme = self.get_object()
        context['weeks'] = SchemeWeek.objects.filter(scheme=scheme).order_by('week_number')
        context['can_submit'] = not scheme.is_submitted
        return context


@method_decorator(login_required, name='dispatch')
class TeacherSchemeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Teachers update scheme of work"""
    model = SchemeOfWork
    form_class = SchemeOfWorkForm
    template_name = 'teachers/scheme/scheme_form.html'

    def test_func(self):
        try:
            teacher = self.request.user.teacher_profile
            scheme = self.get_object()
            return scheme.teacher == teacher and teacher_has_permission(teacher, 'edit_scheme') and not scheme.is_submitted
        except:
            return False

    def get_success_url(self):
        return reverse_lazy('teacher_scheme_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Scheme of work updated successfully.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class SchemeWeekCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a week in scheme of work"""
    model = SchemeWeek
    form_class = SchemeWeekForm
    template_name = 'teachers/scheme/week_form.html'

    def test_func(self):
        try:
            teacher = self.request.user.teacher_profile
            scheme = SchemeOfWork.objects.get(pk=self.kwargs.get('scheme_id'))
            return scheme.teacher == teacher and teacher_has_permission(teacher, 'edit_scheme') and not scheme.is_submitted
        except:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scheme = SchemeOfWork.objects.get(pk=self.kwargs.get('scheme_id'))
        context['scheme'] = scheme
        # Suggest next week number
        last_week = SchemeWeek.objects.filter(scheme=scheme).order_by('-week_number').first()
        context['next_week_number'] = (last_week.week_number + 1) if last_week else 1
        return context

    def form_valid(self, form):
        form.instance.scheme_id = self.kwargs.get('scheme_id')
        messages.success(self.request, 'Week added to scheme.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('teacher_scheme_detail', kwargs={'pk': self.kwargs.get('scheme_id')})


@method_decorator(login_required, name='dispatch')
class SchemeWeekUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update a week in scheme of work"""
    model = SchemeWeek
    form_class = SchemeWeekForm
    template_name = 'teachers/scheme/week_form.html'

    def test_func(self):
        try:
            teacher = self.request.user.teacher_profile
            week = self.get_object()
            return (
                week.scheme.teacher == teacher and
                teacher_has_permission(teacher, 'edit_scheme') and
                not week.scheme.is_submitted
            )
        except:
            return False

    def get_success_url(self):
        return reverse_lazy('teacher_scheme_detail', kwargs={'pk': self.object.scheme.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Week updated successfully.')
        return super().form_valid(form)


@login_required
def mark_week_complete(request, week_id):
    """Mark a week as completed"""
    week = get_object_or_404(SchemeWeek, pk=week_id)
    
    try:
        teacher = request.user.teacher_profile
        if week.scheme.teacher != teacher or week.scheme.is_submitted:
            messages.error(request, 'You do not have permission to complete this week.')
            return redirect('home')
        
        if not teacher_has_permission(teacher, 'edit_scheme'):
            messages.error(request, 'You do not have permission.')
            return redirect('home')
    except:
        messages.error(request, 'You must be a teacher to access this page.')
        return redirect('home')

    week.is_completed = True
    week.completed_date = timezone.now().date()
    week.save()

    messages.success(request, f'Week {week.week_number} marked as completed.')
    return redirect('teacher_scheme_detail', pk=week.scheme.pk)


@login_required
def mark_week_incomplete(request, week_id):
    """Mark a week as not completed"""
    week = get_object_or_404(SchemeWeek, pk=week_id)
    
    try:
        teacher = request.user.teacher_profile
        if week.scheme.teacher != teacher or week.scheme.is_submitted:
            messages.error(request, 'You do not have permission to mark this week incomplete.')
            return redirect('home')
        
        if not teacher_has_permission(teacher, 'edit_scheme'):
            messages.error(request, 'You do not have permission.')
            return redirect('home')
    except:
        messages.error(request, 'You must be a teacher to access this page.')
        return redirect('home')

    week.is_completed = False
    week.completed_date = None
    week.save()

    messages.success(request, f'Week {week.week_number} marked as not completed.')
    return redirect('teacher_scheme_detail', pk=week.scheme.pk)


@login_required
def acknowledge_week_completion(request, week_id):
    """Teacher acknowledges week completion (reports it to admin)"""
    week = get_object_or_404(SchemeWeek, pk=week_id)
    
    try:
        teacher = request.user.teacher_profile
        if week.scheme.teacher != teacher:
            messages.error(request, 'You do not have permission.')
            return redirect('home')
        
        if not teacher_has_permission(teacher, 'edit_scheme'):
            messages.error(request, 'You do not have permission.')
            return redirect('home')
    except:
        messages.error(request, 'You must be a teacher to access this page.')
        return redirect('home')

    if not week.is_completed:
        messages.error(request, 'Please mark the week as completed before acknowledging.')
        return redirect('teacher_scheme_detail', pk=week.scheme.pk)

    week.is_acknowledged = True
    week.acknowledged_at = timezone.now()
    week.save()

    messages.success(request, f'Week {week.week_number} acknowledged. Waiting for admin approval.')
    return redirect('teacher_scheme_detail', pk=week.scheme.pk)


@login_required
def approve_week_completion(request, week_id):
    """Admin approves week completion"""
    week = get_object_or_404(SchemeWeek, pk=week_id)
    
    try:
        if not user_is_admin(request.user):
            messages.error(request, 'You do not have permission to approve weeks.')
            return redirect('home')
    except:
        messages.error(request, 'You do not have permission.')
        return redirect('home')

    if request.method == 'POST':
        admin_notes = request.POST.get('admin_notes', '').strip()
        
        week.is_approved = True
        week.approved_by = request.user
        week.approved_at = timezone.now()
        week.admin_notes = admin_notes
        week.save()

        messages.success(request, f'Week {week.week_number} approved successfully.')
    
    return redirect('teacher_scheme_detail', pk=week.scheme.pk)


@method_decorator(login_required, name='dispatch')
class AdminSchemeWeeksListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin view pending week acknowledgements"""
    template_name = 'admin/scheme_weeks_pending.html'

    def test_func(self):
        return user_is_admin(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get pending weeks (acknowledged but not approved)
        pending_weeks = SchemeWeek.objects.filter(
            is_acknowledged=True,
            is_approved=False
        ).select_related('scheme__teacher__user', 'scheme__school_class', 'scheme__subject').order_by('-acknowledged_at')
        
        # Get approved weeks
        approved_weeks = SchemeWeek.objects.filter(
            is_approved=True
        ).select_related('scheme__teacher__user', 'scheme__school_class', 'scheme__subject').order_by('-approved_at')[:20]
        
        context['pending_weeks'] = pending_weeks
        context['approved_weeks'] = approved_weeks
        
        return context


@login_required
def submit_scheme_for_approval(request, scheme_id):
    """Submit scheme for admin approval"""
    scheme = get_object_or_404(SchemeOfWork, pk=scheme_id)
    
    try:
        teacher = request.user.teacher_profile
        if scheme.teacher != teacher:
            messages.error(request, 'You do not have permission to submit this scheme.')
            return redirect('home')
        
        if not teacher_has_permission(teacher, 'submit_scheme'):
            messages.error(request, 'You do not have permission to submit schemes.')
            return redirect('home')
    except:
        messages.error(request, 'You must be a teacher to access this page.')
        return redirect('home')

    if scheme.is_submitted:
        messages.warning(request, 'This scheme has already been submitted.')
        return redirect('teacher_scheme_detail', pk=scheme_id)

    scheme.is_submitted = True
    scheme.submitted_at = timezone.now()
    scheme.save()

    messages.success(request, 'Scheme submitted for approval. Awaiting admin acknowledgement.')
    return redirect('teacher_scheme_detail', pk=scheme_id)


# ==================== ADMIN: SCHEME APPROVAL ====================

@method_decorator(login_required, name='dispatch')
class AdminSchemeListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Admin view all submitted schemes"""
    model = SchemeOfWork
    template_name = 'teachers/admin/scheme_list.html'
    context_object_name = 'schemes'
    paginate_by = 20

    def test_func(self):
        return user_is_admin(self.request.user)

    def get_queryset(self):
        queryset = SchemeOfWork.objects.filter(is_submitted=True).select_related(
            'teacher__user', 'school_class', 'subject', 'term'
        )
        
        # Filter by approval status
        status = self.request.GET.get('status')
        if status == 'approved':
            queryset = queryset.filter(is_approved=True)
        elif status == 'pending':
            queryset = queryset.filter(is_approved=False)
        
        return queryset.order_by('-submitted_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = SchemeOfWork.objects.filter(is_submitted=True, is_approved=False).count()
        context['approved_count'] = SchemeOfWork.objects.filter(is_approved=True).count()
        return context


@method_decorator(login_required, name='dispatch')
class AdminSchemeDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Admin view scheme details"""
    model = SchemeOfWork
    template_name = 'teachers/admin/scheme_detail.html'
    context_object_name = 'scheme'

    def test_func(self):
        return user_is_admin(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scheme = self.get_object()
        context['weeks'] = SchemeWeek.objects.filter(scheme=scheme).order_by('week_number')
        return context


@login_required
def approve_scheme(request, scheme_id):
    """Admin approves a submitted scheme"""
    if not user_is_admin(request.user):
        messages.error(request, 'You do not have permission to approve schemes.')
        return redirect('home')

    scheme = get_object_or_404(SchemeOfWork, pk=scheme_id)
    
    if not scheme.is_submitted:
        messages.warning(request, 'This scheme has not been submitted yet.')
        return redirect('home')

    scheme.is_approved = True
    scheme.approved_at = timezone.now()
    scheme.approved_by = request.user
    scheme.approval_notes = request.POST.get('approval_notes', '')
    scheme.save()

    messages.success(request, f'Scheme approved for {scheme.teacher}.')
    return redirect('admin_scheme_detail', pk=scheme_id)


@login_required
def reject_scheme(request, scheme_id):
    """Admin rejects a submitted scheme"""
    if not user_is_admin(request.user):
        messages.error(request, 'You do not have permission to reject schemes.')
        return redirect('home')

    scheme = get_object_or_404(SchemeOfWork, pk=scheme_id)
    
    if not scheme.is_submitted:
        messages.warning(request, 'This scheme has not been submitted yet.')
        return redirect('home')

    scheme.is_submitted = False
    scheme.submitted_at = None
    scheme.approval_notes = request.POST.get('approval_notes', 'Rejected by admin for revision.')
    scheme.save()

    messages.success(request, f'Scheme returned to {scheme.teacher} for revision.')
    return redirect('admin_scheme_list')
