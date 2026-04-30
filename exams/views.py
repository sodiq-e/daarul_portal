from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from .models import Subject, Exam
from .forms import SubjectForm, ExamForm
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