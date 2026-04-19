from django.urls import path
from . import views

urlpatterns = [
    path('', views.results_home, name='results_home'),
    path('class/<int:class_id>/<int:term_id>/', views.class_results, name='class_results'),
    path('student/<int:student_id>/<int:term_id>/', views.student_report_card, name='student_report_card'),
    path('broadsheet/<int:class_id>/<int:term_id>/', views.broadsheet, name='broadsheet'),
    path('lookup/', views.student_results_by_admission, name='student_results_lookup'),
    # Legacy URLs for backward compatibility
    path('report/<int:student_id>/<int:exam_id>/', views.report_card, name='report_card'),
    path('promotions/', views.promotions_list, name='promotions_list'),
    path('promote/<int:student_id>/<int:exam_id>/', views.promote_student, name='promote_student'),
]
