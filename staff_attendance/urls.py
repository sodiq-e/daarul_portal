from django.urls import path
from . import views

app_name = 'staff_attendance'

urlpatterns = [
    path('', views.StaffAttendanceDashboardView.as_view(), name='dashboard'),
    path('history/', views.AttendanceHistoryView.as_view(), name='history'),
    path('monthly-report/', views.MonthlyReportView.as_view(), name='monthly_report'),
    path('settings/', views.AttendanceSettingsView.as_view(), name='settings'),
    path('student-settings/', views.StudentAttendanceSettingsView.as_view(), name='student_settings'),
    path('api/clock-in/', views.StaffAttendanceClockInAPI.as_view(), name='api_clock_in'),
    path('api/clock-out/', views.StaffAttendanceClockOutAPI.as_view(), name='api_clock_out'),
    path('api/sync/', views.StaffAttendanceSyncAPI.as_view(), name='api_sync'),
]
