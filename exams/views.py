from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Subject, Exam
from .forms import SubjectForm, ExamForm


# Subject Views
class SubjectListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Subject
    template_name = 'exams/subject_list.html'
    context_object_name = 'subjects'
    paginate_by = 20

    def test_func(self):
        return self.request.user.profile.is_approved

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = (
            self.request.user.profile.is_approved and
            self.request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()
        )
        return context


class SubjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Subject
    template_name = 'exams/subject_detail.html'
    context_object_name = 'subject'

    def test_func(self):
        return self.request.user.profile.is_approved

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = (
            self.request.user.profile.is_approved and
            self.request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()
        )
        return context


class SubjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'exams/subject_form.html'
    success_url = reverse_lazy('subject_list')

    def test_func(self):
        return self.request.user.profile.is_approved and self.request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()

    def form_valid(self, form):
        messages.success(self.request, 'Subject created successfully.')
        return super().form_valid(form)


class SubjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'exams/subject_form.html'
    success_url = reverse_lazy('subject_list')

    def test_func(self):
        return self.request.user.profile.is_approved and self.request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()

    def form_valid(self, form):
        messages.success(self.request, 'Subject updated successfully.')
        return super().form_valid(form)


class SubjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Subject
    template_name = 'exams/subject_confirm_delete.html'
    success_url = reverse_lazy('subject_list')

    def test_func(self):
        return self.request.user.profile.is_approved and self.request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()

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
        return self.request.user.profile.is_approved

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = (
            self.request.user.profile.is_approved and
            self.request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()
        )
        return context


class ExamDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Exam
    template_name = 'exams/exam_detail.html'
    context_object_name = 'exam'

    def test_func(self):
        return self.request.user.profile.is_approved

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = (
            self.request.user.profile.is_approved and
            self.request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()
        )
        return context


class ExamCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'
    success_url = reverse_lazy('exam_list')

    def test_func(self):
        return self.request.user.profile.is_approved and self.request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()

    def form_valid(self, form):
        messages.success(self.request, 'Exam created successfully.')
        return super().form_valid(form)


class ExamUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'
    success_url = reverse_lazy('exam_list')

    def test_func(self):
        return self.request.user.profile.is_approved and self.request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()

    def form_valid(self, form):
        messages.success(self.request, 'Exam updated successfully.')
        return super().form_valid(form)


class ExamDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Exam
    template_name = 'exams/exam_confirm_delete.html'
    success_url = reverse_lazy('exam_list')

    def test_func(self):
        return self.request.user.profile.is_approved and self.request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Exam deleted successfully.')
        return super().delete(request, *args, **kwargs)