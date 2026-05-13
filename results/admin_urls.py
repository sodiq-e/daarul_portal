from django.urls import path
from . import admin_views

app_name = 'results_admin'

urlpatterns = [
    path('', admin_views.results_settings_dashboard, name='dashboard'),
    path('academic-sessions/', admin_views.manage_academic_sessions, name='academic_sessions'),
    path('subjects/', admin_views.bulk_manage_subjects, name='bulk_subjects'),
    path('grade-scales/', admin_views.bulk_manage_grade_scales, name='bulk_grade_scales'),
    path('templates/', admin_views.bulk_create_result_templates, name='bulk_templates'),
    path('class-subjects/', admin_views.bulk_assign_class_subjects, name='bulk_class_subjects'),
    path('publish-results/', admin_views.manage_result_publication, name='publish_results'),
]
