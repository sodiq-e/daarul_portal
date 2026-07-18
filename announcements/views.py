from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Announcement, AnnouncementCategory
from django.db.models import Q
from .forms import AnnouncementForm
from pages.models import Page


class AnnouncementListView(ListView):
    model = Announcement
    template_name = 'announcements/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 10

    def get_queryset(self):
        qs = Announcement.objects.filter(is_active=True).order_by('-created_at')
        q = self.request.GET.get('q')
        cat = self.request.GET.get('category')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(excerpt__icontains=q) | Q(content__icontains=q))
        if cat:
            qs = qs.filter(category__id=cat)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pages'] = Page.objects.filter(
            is_published=True,
            url_prefix='announcements',
            show_in_navigation=True
        )
        context['categories'] = AnnouncementCategory.objects.all()
        context['q'] = self.request.GET.get('q', '')
        context['selected_category'] = self.request.GET.get('category', '')
        return context


class AnnouncementDetailView(DetailView):
    model = Announcement
    template_name = 'announcements/announcement_detail.html'
    context_object_name = 'announcement'

    def get_queryset(self):
        return Announcement.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pages'] = Page.objects.filter(
            is_published=True,
            url_prefix='announcements',
            show_in_navigation=True
        )
        return context


class AnnouncementCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Announcement
    template_name = 'announcements/announcement_form.html'
    form_class = AnnouncementForm
    success_url = reverse_lazy('announcement_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Announcement created successfully.')
        return super().form_valid(form)


class AnnouncementUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Announcement
    template_name = 'announcements/announcement_form.html'
    form_class = AnnouncementForm
    success_url = reverse_lazy('announcement_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(self.request, 'Announcement updated successfully.')
        return super().form_valid(form)


class AnnouncementDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Announcement
    template_name = 'announcements/announcement_confirm_delete.html'
    success_url = reverse_lazy('announcement_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Announcement deleted successfully.')
        return super().delete(request, *args, **kwargs)
