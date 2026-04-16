from django import forms
from .models import AttendanceRecord


class AttendanceRecordForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ['student', 'date', 'present']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }