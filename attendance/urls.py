from django.urls import path
from . import views

urlpatterns = [
    path('', views.AttendanceRecordListView.as_view(), name='attendance_list'),
    path('<int:pk>/', views.AttendanceRecordDetailView.as_view(), name='attendance_detail'),
    path('add/', views.AttendanceRecordCreateView.as_view(), name='attendance_add'),
    path('<int:pk>/edit/', views.AttendanceRecordUpdateView.as_view(), name='attendance_edit'),
    path('<int:pk>/delete/', views.AttendanceRecordDeleteView.as_view(), name='attendance_delete'),
]