from django.urls import path
from . import views

app_name = 'teacher_cbt'

urlpatterns = [
    path('', views.TeacherCBTDashboardView.as_view(), name='dashboard'),
    path('manage/', views.TeacherCBTExamListView.as_view(), name='manage'),
    path('manage/add/', views.TeacherCBTExamCreateView.as_view(), name='exam_add'),
    path('manage/<int:pk>/edit/', views.TeacherCBTExamUpdateView.as_view(), name='exam_edit'),
    path('attempts/', views.TeacherCBTAttemptListView.as_view(), name='attempt_list'),
    path('attempts/<uuid:uuid>/', views.attempt_detail, name='attempt_detail'),
    path('analytics/', views.TeacherCBTAnalyticsView.as_view(), name='analytics'),
]
