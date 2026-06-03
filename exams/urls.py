from django.urls import path
from . import views

urlpatterns = [
    # Subjects
    path('subjects/', views.SubjectListView.as_view(), name='subject_list'),
    path('subjects/select-class/', views.SelectClassForSubjectsView.as_view(), name='select_class_for_subjects'),
    path('subjects/<int:pk>/', views.SubjectDetailView.as_view(), name='subject_detail'),
    path('subjects/add/', views.SubjectCreateView.as_view(), name='subject_add'),
    path('subjects/<int:pk>/edit/', views.SubjectUpdateView.as_view(), name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.SubjectDeleteView.as_view(), name='subject_delete'),

    # Exams
    path('exams/', views.ExamListView.as_view(), name='exam_list'),
    path('exams/<int:pk>/', views.ExamDetailView.as_view(), name='exam_detail'),
    path('exams/add/', views.ExamCreateView.as_view(), name='exam_add'),
    path('exams/<int:pk>/edit/', views.ExamUpdateView.as_view(), name='exam_edit'),
    path('exams/<int:pk>/delete/', views.ExamDeleteView.as_view(), name='exam_delete'),

    # Teacher exam paper workflow
    path('exam-papers/', views.TeacherExamPaperListView.as_view(), name='exam_paper_list'),
    path('exam-papers/add/', views.TeacherExamPaperCreateView.as_view(), name='exam_paper_add'),
    path('exam-papers/<int:pk>/edit/', views.TeacherExamPaperEditView.as_view(), name='exam_paper_edit'),
    path('exam-papers/<int:pk>/', views.TeacherExamPaperDetailView.as_view(), name='exam_paper_detail'),
    path('exam-papers/save-draft/', views.ExamPaperSaveView.as_view(), name='exam_paper_save'),
    path('exam-papers/submit/', views.ExamPaperSubmitView.as_view(), name='exam_paper_submit'),

    # Admin review workflow
    path('admin/exam-papers/', views.AdminExamPaperListView.as_view(), name='admin_exam_paper_list'),
    path('admin/exam-papers/<int:pk>/', views.AdminExamPaperDetailView.as_view(), name='admin_exam_paper_detail'),
    path('admin/exam-papers/<int:pk>/action/', views.AdminExamPaperActionView.as_view(), name='admin_exam_paper_action'),
]