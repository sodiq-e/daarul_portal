from django.contrib import admin
from django.utils.html import format_html
from .models import AttendanceRecord, AttendanceSession, AttendanceHoliday, AttendanceSettings


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'school_class', 'date', 'morning_status', 'afternoon_status', 'marked_by', 'marked_at')
    list_filter = ('present', 'date', 'school_class', 'marked_by')
    search_fields = ('student__admission_no', 'student__surname', 'student__other_names')
    date_hierarchy = 'date'
    readonly_fields = ('marked_at',)
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'school_class', 'date')
        }),
        ('Attendance Marking', {
            'fields': ('morning_present', 'afternoon_present', 'present')
        }),
        ('Additional Information', {
            'fields': ('notes', 'marked_by', 'marked_at')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'school_class', 'marked_by')

    def morning_status(self, obj):
        if obj.morning_present:
            return format_html('<span style="color: green;">✓ Present</span>')
        return format_html('<span style="color: red;">✗ Absent</span>')
    morning_status.short_description = 'Morning'

    def afternoon_status(self, obj):
        if obj.afternoon_present:
            return format_html('<span style="color: green;">✓ Present</span>')
        return format_html('<span style="color: red;">✗ Absent</span>')
    afternoon_status.short_description = 'Afternoon'


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('school_class', 'date', 'weekday', 'teacher', 'attendance_summary', 'day_type')
    list_filter = ('date', 'school_class', 'teacher', 'day_type')
    search_fields = ('school_class__class_name', 'teacher__user__username')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'week_number')
    fieldsets = (
        ('Class & Date Information', {
            'fields': ('school_class', 'date', 'weekday', 'week_number')
        }),
        ('Attendance Summary', {
            'fields': ('total_students', 'present_count', 'absent_count', 'day_type')
        }),
        ('Teacher Information', {
            'fields': ('teacher', 'created_at')
        }),
    )

    def attendance_summary(self, obj):
        percentage = round((obj.present_count / obj.total_students * 100), 1) if obj.total_students > 0 else 0
        return format_html(
            '<strong>{}/{}</strong> ({}%)',
            obj.present_count,
            obj.total_students,
            f"{percentage:.1f}",
    )
    attendance_summary.short_description = 'Present/Total (%)'



@admin.register(AttendanceHoliday)
class AttendanceHolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'holiday_type', 'date_range', 'is_active', 'duration_days')
    list_filter = ('holiday_type', 'is_active', 'start_date')
    search_fields = ('name', 'description')
    date_hierarchy = 'start_date'
    fieldsets = (
        ('Holiday Information', {
            'fields': ('name', 'holiday_type', 'description')
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date'),
            'description': 'Define the start and end dates for this holiday period'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    def date_range(self, obj):
        return format_html(
            '<strong>{}</strong> to <strong>{}</strong>',
            obj.start_date.strftime('%b %d, %Y'),
            obj.end_date.strftime('%b %d, %Y')
        )
    date_range.short_description = 'Holiday Period'

    def duration_days(self, obj):
        delta = obj.end_date - obj.start_date
        days = delta.days + 1  # Include both start and end dates
        return format_html('<span style="color: #0066cc;"><strong>{}</strong> day{}</span>',
                          days, 's' if days > 1 else '')
    duration_days.short_description = 'Duration'


@admin.register(AttendanceSettings)
class AttendanceSettingsAdmin(admin.ModelAdmin):
    list_display = ('config_summary', 'minimum_attendance_percentage', 'last_updated')
    fieldsets = (
        ('Term-Related Settings', {
            'fields': ('enable_term_date_restriction',),
            'description': 'Control whether attendance can only be marked within configured term dates'
        }),
        ('Attendance Marking', {
            'fields': ('allow_retroactive_marking', 'school_has_morning_session', 'school_has_afternoon_session'),
            'description': 'Configure what sessions your school operates and marking permissions'
        }),
        ('Attendance Standards', {
            'fields': ('minimum_attendance_percentage',),
            'description': 'Define the minimum attendance percentage required for students'
        }),
        ('Holiday Management', {
            'fields': ('auto_mark_holidays_as_absent',),
            'description': 'Automatic holiday handling options'
        }),
        ('Reporting', {
            'fields': ('attendance_calculation_method',),
            'description': 'How attendance percentage is calculated in reports'
        }),
        ('Notifications', {
            'fields': ('send_low_attendance_alerts',),
            'description': 'Send alerts when attendance drops below minimum threshold'
        }),
        ('Admin Information', {
            'fields': ('last_updated_by',),
            'classes': ('collapse',),
            'description': 'Read-only metadata'
        }),
    )
    readonly_fields = (
      'created_at',
      'week_number',
    )

    def config_summary(self, obj):
        return "📋 Attendance Configuration"
    config_summary.short_description = 'Settings'

    def has_add_permission(self, request):
        # Only allow one settings object
        return not AttendanceSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of settings
        return False

