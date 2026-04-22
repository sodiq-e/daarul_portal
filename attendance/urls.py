from django.urls import path
from . import views

urlpatterns = [
    path('', views.AttendanceRecordListView.as_view(), name='attendance_list'),
    path('<int:pk>/', views.AttendanceRecordDetailView.as_view(), name='attendance_detail'),
    path('add/', views.AttendanceRecordCreateView.as_view(), name='attendance_add'),
    path('<int:pk>/edit/', views.AttendanceRecordUpdateView.as_view(), name='attendance_edit'),
    path('<int:pk>/delete/', views.AttendanceRecordDeleteView.as_view(), name='attendance_delete'),
    
    # Teacher Attendance Views
    path('teacher/mark/', views.TeacherAttendanceMarkView.as_view(), name='teacher_mark_attendance'),
    path('teacher/list/', views.TeacherAttendanceListView.as_view(), name='teacher_attendance_list'),
    path('teacher/report/', views.TeacherAttendanceReportView.as_view(), name='teacher_attendance_report'),
]