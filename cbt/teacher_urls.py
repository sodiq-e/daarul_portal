from django.urls import path
from . import views
from .question_bank_views import (
    TeacherQuestionBankListView,
    QuestionBankCreateView,
    QuestionBankUpdateView,
    QuestionBankDeleteView,
    QuestionBankDetailView,
    QuestionCreateView,
    QuestionUpdateView,
    QuestionDeleteView,
    QuestionCloneView,
    QuestionSearchAPIView,
)

app_name = 'teacher_cbt'

urlpatterns = [
    # Dashboard and exams
    path('', views.TeacherCBTDashboardView.as_view(), name='dashboard'),
    path('manage/', views.TeacherCBTExamListView.as_view(), name='manage'),
    path('manage/add/', views.TeacherCBTExamCreateView.as_view(), name='exam_add'),
    path('manage/<int:pk>/edit/', views.TeacherCBTExamUpdateView.as_view(), name='exam_edit'),
    path('attempts/', views.TeacherCBTAttemptListView.as_view(), name='attempt_list'),
    path('attempts/<uuid:uuid>/', views.attempt_detail, name='attempt_detail'),
    path('analytics/', views.TeacherCBTAnalyticsView.as_view(), name='analytics'),
    
    # Question banks
    path('question-banks/', TeacherQuestionBankListView.as_view(), name='question_banks'),
    path('question-banks/add/', QuestionBankCreateView.as_view(), name='question_bank_add'),
    path('question-banks/<int:pk>/', QuestionBankDetailView.as_view(), name='question_bank_detail'),
    path('question-banks/<int:pk>/edit/', QuestionBankUpdateView.as_view(), name='question_bank_edit'),
    path('question-banks/<int:pk>/delete/', QuestionBankDeleteView.as_view(), name='question_bank_delete'),
    
    # Questions in banks
    path('question-banks/<int:bank_pk>/questions/add/', QuestionCreateView.as_view(), name='question_add'),
    path('questions/<int:pk>/edit/', QuestionUpdateView.as_view(), name='question_edit'),
    path('questions/<int:pk>/delete/', QuestionDeleteView.as_view(), name='question_delete'),
    path('questions/<int:question_pk>/clone/', QuestionCloneView.as_view(), name='question_clone'),
    path('manage/<int:exam_pk>/questions/', views.ManageExamQuestionsView.as_view(), name='manage_questions'),
    
    # API endpoints
    path('api/search-questions/', QuestionSearchAPIView.as_view(), name='search_questions'),
]
