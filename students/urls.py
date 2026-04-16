from django.urls import path
from . import views

urlpatterns = [
    path('apply/', views.StudentApplicationCreateView.as_view(), name='student_application'),
    path('applications/', views.StudentApplicationListView.as_view(), name='student_application_list'),
    path('applications/<int:pk>/', views.StudentApplicationDetailView.as_view(), name='student_application_detail'),
    path('applications/<int:pk>/edit/', views.StudentApplicationUpdateView.as_view(), name='student_application_edit'),
    path('', views.StudentListView.as_view(), name='student_list'),
    path('<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('add/', views.StudentCreateView.as_view(), name='student_add'),
    path('<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_edit'),
    path('<int:pk>/status/', views.student_status_update, name='student_status_update'),
]