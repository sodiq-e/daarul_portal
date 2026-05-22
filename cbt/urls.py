from django.urls import path
from . import views

app_name = 'cbt'

urlpatterns = [
    path('teacher/exams/', views.CBTExamListView.as_view(), name='exam_list'),
    path('teacher/exams/add/', views.CBTExamCreateView.as_view(), name='exam_add'),
    path('teacher/exams/<int:pk>/edit/', views.CBTExamUpdateView.as_view(), name='exam_edit'),
    path('teacher/exams/<int:exam_pk>/questions/', views.CBTQuestionListView.as_view(), name='question_list'),
    path('teacher/exams/<int:exam_pk>/questions/add/', views.CBTQuestionCreateView.as_view(), name='question_add'),
    path('teacher/exams/questions/<int:question_pk>/edit/', views.CBTQuestionUpdateView.as_view(), name='question_edit'),

    path('practice/', views.PracticeExamListView.as_view(), name='practice_exam_list'),
    path('practice/<int:pk>/start/', views.start_practice_exam, name='practice_exam_start'),

    path('real/', views.RealExamListView.as_view(), name='real_exam_list'),
    path('real/<int:pk>/', views.real_exam_detail, name='real_exam_detail'),
    path('real/<int:pk>/start/', views.start_real_exam, name='real_exam_start'),

    path('attempt/<uuid:uuid>/', views.attempt_detail, name='attempt_detail'),
    path('api/save-answer/', views.api_save_answer, name='api_save_answer'),
    path('api/submit-attempt/', views.api_submit_attempt, name='api_submit_attempt'),
    path('api/generate-ss1-questions/', views.api_generate_ss1_questions, name='api_generate_ss1_questions'),
]
