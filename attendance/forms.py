from django import forms
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from exams.models import Term
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
            'morning_session_start',
            'morning_session_end',
            'afternoon_session_start',
            'afternoon_session_end',
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
            'morning_session_start': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
            'morning_session_end': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
            'afternoon_session_start': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
            'afternoon_session_end': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
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
            'morning_session_start': 'Morning session starts',
            'morning_session_end': 'Morning session ends',
            'afternoon_session_start': 'Afternoon session starts',
            'afternoon_session_end': 'Afternoon session ends',
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('school_has_morning_session'):
            morning_start = cleaned_data.get('morning_session_start')
            morning_end = cleaned_data.get('morning_session_end')
            if morning_start and morning_end and morning_start >= morning_end:
                raise ValidationError('Morning session end time must be after its start time.')
        if cleaned_data.get('school_has_afternoon_session'):
            afternoon_start = cleaned_data.get('afternoon_session_start')
            afternoon_end = cleaned_data.get('afternoon_session_end')
            if afternoon_start and afternoon_end and afternoon_start >= afternoon_end:
                raise ValidationError('Afternoon session end time must be after its start time.')
        return cleaned_data


class TermDateForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ['start_date', 'end_date', 'next_term_begins_date']
        widgets = {
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'next_term_begins_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'start_date': 'Term begins',
            'end_date': 'Term ends',
            'next_term_begins_date': 'Next term begins',
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise ValidationError('Term end date must be on or after the term start date.')
        return cleaned_data


TermDateFormSet = modelformset_factory(
    Term,
    form=TermDateForm,
    extra=0,
)
