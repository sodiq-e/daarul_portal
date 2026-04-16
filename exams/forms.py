from django import forms
from .models import Subject, Exam


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code']


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }