from django.urls import path
from . import views

urlpatterns = [
    path('', views.results_home, name='results_home'),
    path('class/<int:class_id>/<int:term_id>/', views.class_results, name='class_results'),
    path('student/<int:student_id>/<int:term_id>/', views.student_report_card, name='student_report_card'),
    path('broadsheet/<int:class_id>/<int:term_id>/', views.broadsheet, name='broadsheet'),
    path('lookup/', views.student_results_by_admission, name='student_results_lookup'),
    
    # Teacher results views
    path('teacher/results/', views.teacher_results_list, name='teacher_results_list'),
    path('teacher/class/<int:class_id>/<int:term_id>/', views.teacher_class_results, name='teacher_class_results'),
    path('teacher/class/<int:class_id>/<int:term_id>/bulk-entry/', views.bulk_result_entry, name='bulk_result_entry'),
    path('teacher/edit/<int:result_id>/', views.teacher_edit_student_result, name='teacher_edit_result'),
    path('teacher/print/<int:student_id>/<int:term_id>/', views.teacher_print_results, name='teacher_print_results'),
    path('teacher/broadsheet/<int:class_id>/<int:term_id>/', views.teacher_print_broadsheet, name='teacher_print_broadsheet'),
    
    # Teacher report card editing
    path('teacher/report-card/<int:student_id>/<int:term_id>/edit/', views.teacher_edit_report_card, name='teacher_edit_report_card'),
    path('teacher/report-card/<int:student_id>/<int:term_id>/comments/', views.teacher_view_report_card_comments, name='teacher_report_card_comments'),
    
    # Legacy URLs for backward compatibility
    path('report/<int:student_id>/<int:exam_id>/', views.report_card, name='report_card'),
    path('promotions/', views.promotions_list, name='promotions_list'),
    path('promote/<int:student_id>/<int:exam_id>/', views.promote_student, name='promote_student'),
]
