from django.contrib import admin
from .models import AttendanceSettings, StaffAttendance


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
