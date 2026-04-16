from django.urls import path
from . import views

urlpatterns = [
    path('', views.results_home, name='results_home'),
    path('report/<int:student_id>/<int:exam_id>/', views.report_card, name='report_card'),
    path('promotions/', views.promotions_list, name='promotions_list'),
    path('promote/<int:student_id>/<int:exam_id>/', views.promote_student, name='promote_student'),
    path('broadsheet/<int:exam_id>/', views.broadsheet, name='broadsheet'),
]
