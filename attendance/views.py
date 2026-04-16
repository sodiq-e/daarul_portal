from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import AttendanceRecord
from .forms import AttendanceRecordForm


class AttendanceRecordListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = AttendanceRecord
    template_name = 'attendance/attendance_list.html'
    context_object_name = 'attendance_records'
    paginate_by = 20
    ordering = ['-date', 'student']

    def test_func(self):
        return self.request.user.profile.is_approved

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = (
            self.request.user.profile.is_approved and
            self.request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()
        )
        return context


class AttendanceRecordDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = AttendanceRecord
    template_name = 'attendance/attendance_detail.html'
    context_object_name = 'attendance_record'

    def test_func(self):
        return self.request.user.profile.is_approved

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = (
            self.request.user.profile.is_approved and
            self.request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()
        )
        return context


class AttendanceRecordCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = AttendanceRecord
    form_class = AttendanceRecordForm
    template_name = 'attendance/attendance_form.html'
    success_url = reverse_lazy('attendance_list')

    def test_func(self):
        return self.request.user.profile.is_approved and self.request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()

    def form_valid(self, form):
        messages.success(self.request, 'Attendance record created successfully.')
        return super().form_valid(form)


class AttendanceRecordUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = AttendanceRecord
    form_class = AttendanceRecordForm
    template_name = 'attendance/attendance_form.html'
    success_url = reverse_lazy('attendance_list')

    def test_func(self):
        return self.request.user.profile.is_approved and self.request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()

    def form_valid(self, form):
        messages.success(self.request, 'Attendance record updated successfully.')
        return super().form_valid(form)


class AttendanceRecordDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = AttendanceRecord
    template_name = 'attendance/attendance_confirm_delete.html'
    success_url = reverse_lazy('attendance_list')

    def test_func(self):
        return self.request.user.profile.is_approved and self.request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Attendance record deleted successfully.')
        return super().delete(request, *args, **kwargs)