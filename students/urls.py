from django.urls import path
from . import views

urlpatterns = [
    # Student Portal - Student Only Views
    path('portal/dashboard/', views.StudentDashboardView.as_view(), name='student_portal_dashboard'),
    path('portal/profile/', views.StudentProfileDetailView.as_view(), name='student_portal_profile'),
    path('portal/results/', views.StudentResultsView.as_view(), name='student_portal_results'),
    path('portal/fees/', views.StudentFeesView.as_view(), name='student_portal_fees'),
    
    # Admin/Staff Views
    path('apply/', views.StudentApplicationCreateView.as_view(), name='student_application'),
    path('applications/', views.StudentApplicationListView.as_view(), name='student_application_list'),
    path('applications/<int:pk>/', views.StudentApplicationDetailView.as_view(), name='student_application_detail'),
    path('applications/<int:pk>/edit/', views.StudentApplicationUpdateView.as_view(), name='student_application_edit'),
    path('applications/<int:pk>/print/', views.print_admission_application, name='print_admission_application'),
    path('', views.StudentListView.as_view(), name='student_list'),
    path('<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('add/', views.StudentCreateView.as_view(), name='student_add'),
    path('<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_edit'),
    path('<int:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),
    path('<int:pk>/status/', views.student_status_update, name='student_status_update'),
]