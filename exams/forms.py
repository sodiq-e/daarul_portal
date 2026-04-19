from django import forms
from .models import (
    Term, Subject, ClassSubject, ExamType, Exam
)
from school_classes.models import SchoolClasses


class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ['name', 'display_name', 'academic_year', 'is_active']


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description', 'is_active']


class ClassSubjectForm(forms.ModelForm):
    class Meta:
        model = ClassSubject
        fields = ['school_class', 'subject', 'is_compulsory', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter subjects that aren't already assigned to this class
        if self.instance and self.instance.school_class:
            existing_subjects = ClassSubject.objects.filter(
                school_class=self.instance.school_class
            ).exclude(pk=self.instance.pk).values_list('subject', flat=True)
            self.fields['subject'].queryset = Subject.objects.exclude(
                pk__in=existing_subjects
            )


class ExamTypeForm(forms.ModelForm):
    class Meta:
        model = ExamType
        fields = ['name', 'assessment_type', 'max_score', 'weight_percentage', 'description', 'is_active']


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'term', 'school_class', 'exam_type', 'date', 'is_active']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter terms to only active ones
        self.fields['term'].queryset = Term.objects.filter(is_active=True)


class AssignSubjectsForm(forms.Form):
    """Form for bulk assigning subjects to a class"""
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Select subjects to assign"
    )
    make_compulsory = forms.BooleanField(
        required=False,
        initial=True,
        label="Make all selected subjects compulsory"
    )