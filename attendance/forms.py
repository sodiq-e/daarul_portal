from django import forms
from .models import AttendanceRecord


class AttendanceRecordForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ['student', 'school_class', 'date', 'morning_present', 'afternoon_present', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'morning_present': forms.CheckboxInput(),
            'afternoon_present': forms.CheckboxInput(),
        }