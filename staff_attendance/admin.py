from django.contrib import admin
from .models import AttendanceSettings, StaffAttendance, StudentAttendanceSettings
from settingsapp.tenant_utils import get_request_tenant


@admin.register(AttendanceSettings)
class AttendanceSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'school_latitude',
        'school_longitude',
        'allowed_radius_meters',
        'normal_clock_in_time',
        'late_after_time',
        'earliest_clock_out_time',
        'enable_gps_verification',
        'enable_clock_out',
        'enable_offline_sync',
        'active',
        'updated_at',
    )
    list_filter = ('active', 'enable_gps_verification', 'enable_clock_out', 'enable_offline_sync')
    readonly_fields = ('updated_at',)
    search_fields = ('school_latitude', 'school_longitude')


@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'teacher',
        'date',
        'clock_in_status',
        'clock_in',
        'clock_out',
        'synced',
        'offline_record',
    )
    list_filter = ('clock_in_status', 'synced', 'offline_record', 'date')
    search_fields = ('teacher__user__username', 'teacher__user__first_name', 'teacher__user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'sync_time')


@admin.register(StudentAttendanceSettings)
class StudentAttendanceSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'enable_student_attendance',
        'require_daily_checkin',
        'allow_parent_reason_submission',
        'absence_threshold_warning',
        'active',
        'updated_at',
    )
    list_filter = (
        'active',
        'enable_student_attendance',
        'require_daily_checkin',
        'allow_parent_reason_submission',
    )
    readonly_fields = ('updated_at',)
    fieldsets = (
        ('Student Attendance', {
            'fields': (
                'enable_student_attendance',
                'require_daily_checkin',
                'allow_parent_reason_submission',
            ),
        }),
        ('Warnings and Status', {
            'fields': ('absence_threshold_warning', 'active'),
        }),
        ('Metadata', {
            'fields': ('tenant', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('updated_at',)

    def save_model(self, request, obj, form, change):
        if obj.tenant_id is None:
            obj.tenant = get_request_tenant(request)
        super().save_model(request, obj, form, change)
