from django import forms
from .models import AttendanceSettings, StudentAttendanceSettings


class AttendanceSettingsForm(forms.ModelForm):
    class Meta:
        model = AttendanceSettings
        fields = [
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
        ]
        widgets = {
            'school_latitude': forms.NumberInput(attrs={'step': '0.000001', 'placeholder': 'Latitude'}),
            'school_longitude': forms.NumberInput(attrs={'step': '0.000001', 'placeholder': 'Longitude'}),
            'allowed_radius_meters': forms.NumberInput(attrs={'min': 50}),
            'normal_clock_in_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'late_after_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'earliest_clock_out_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }


class StudentAttendanceSettingsForm(forms.ModelForm):
    class Meta:
        model = StudentAttendanceSettings
        fields = [
            'enable_student_attendance',
            'require_daily_checkin',
            'allow_parent_reason_submission',
            'absence_threshold_warning',
            'active',
        ]
        widgets = {
            'absence_threshold_warning': forms.NumberInput(attrs={'min': 0}),
        }
