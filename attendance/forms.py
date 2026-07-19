from django import forms
from .models import AttendanceRecord, AttendanceSettings


class AttendanceRecordForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ['student', 'school_class', 'date', 'morning_present', 'afternoon_present', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'morning_present': forms.CheckboxInput(),
            'afternoon_present': forms.CheckboxInput(),
        }


class AttendanceSettingsForm(forms.ModelForm):
    class Meta:
        model = AttendanceSettings
        fields = [
            'enable_term_date_restriction',
            'allow_retroactive_marking',
            'minimum_attendance_percentage',
            'auto_mark_holidays_as_absent',
            'attendance_calculation_method',
            'send_low_attendance_alerts',
            'school_has_morning_session',
            'school_has_afternoon_session',
        ]
        widgets = {
            'minimum_attendance_percentage': forms.NumberInput(attrs={
                'type': 'number',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'class': 'form-control',
            }),
            'attendance_calculation_method': forms.Select(attrs={'class': 'form-select'}),
            'enable_term_date_restriction': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_retroactive_marking': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_mark_holidays_as_absent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'send_low_attendance_alerts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'school_has_morning_session': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'school_has_afternoon_session': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'enable_term_date_restriction': 'Restrict marking to term dates',
            'allow_retroactive_marking': 'Allow retroactive marking',
            'minimum_attendance_percentage': 'Minimum attendance %',
            'auto_mark_holidays_as_absent': 'Auto mark holidays as absent',
            'attendance_calculation_method': 'Attendance calculation method',
            'send_low_attendance_alerts': 'Send low attendance alerts',
            'school_has_morning_session': 'Use morning session',
            'school_has_afternoon_session': 'Use afternoon session',
        }
