from django.contrib import admin
from .models import AttendanceRecord, AttendanceSession


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'school_class', 'date', 'present', 'marked_by', 'marked_at')
    list_filter = ('present', 'date', 'school_class', 'marked_by')
    search_fields = ('student__admission_no', 'student__surname', 'student__other_names')
    date_hierarchy = 'date'
    readonly_fields = ('marked_at',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'school_class', 'marked_by')


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('school_class', 'date', 'teacher', 'total_students', 'present_count', 'absent_count')
    list_filter = ('date', 'school_class', 'teacher')
    search_fields = ('school_class__class_name', 'teacher__user__username')
    date_hierarchy = 'date'
    readonly_fields = ('created_at',)
