from rest_framework import serializers

from .models import StaffAttendance, AttendanceSettings


class StaffAttendanceSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)

    class Meta:
        model = StaffAttendance
        fields = [
            'id',
            'teacher_name',
            'date',
            'clock_in',
            'clock_out',
            'clock_in_status',
            'synced',
            'sync_time',
            'device_info',
            'offline_record',
        ]


class AttendanceSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceSettings
        fields = '__all__'
