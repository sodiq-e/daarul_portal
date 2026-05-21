from django import forms
from .models import AttendanceSettings


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
