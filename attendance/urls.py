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
    path('report/', views.AttendanceReportView.as_view(), name='attendance_report'),
    
    # Student Attendance Views
    path('my-attendance/', views.StudentAttendanceHistoryView.as_view(), name='student_attendance_history'),
    
    # Admin Attendance Settings View
    path('settings/', views.AttendanceSettingsView.as_view(), name='attendance_settings'),
    path('admin/student-settings/', views.AdminStudentAttendanceView.as_view(), name='admin_student_settings'),
    path('api/students-by-class/', views.students_by_class, name='students_by_class'),
    path('api/classes/', views.classes_list, name='classes_list'),
]