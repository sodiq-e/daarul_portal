from django.urls import path
from . import views

app_name = 'student_cbt'

urlpatterns = [
    path('', views.StudentCBTDashboardView.as_view(), name='dashboard'),
    path('practice/', views.StudentCBTPracticeListView.as_view(), name='practice_list'),
    path('practice/<int:pk>/start/', views.start_practice_exam, name='practice_start'),
    path('exam/<int:pk>/', views.real_exam_detail, name='exam_detail'),
    path('exam/<int:pk>/start/', views.start_real_exam, name='exam_start'),
    path('attempts/', views.StudentCBTAttemptListView.as_view(), name='attempt_list'),
    path('results/', views.StudentCBTResultListView.as_view(), name='result_list'),
    path('attempt/<uuid:uuid>/', views.attempt_detail, name='attempt_detail'),
]
