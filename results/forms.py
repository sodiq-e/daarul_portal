from django import forms
from .models import (
    GradeScale, ResultTemplate, StudentResult, ReportCardComment
)
from exams.models import Term
from school_classes.models import SchoolClasses


class GradeScaleForm(forms.ModelForm):
    class Meta:
        model = GradeScale
        fields = ['name', 'min_score', 'max_score', 'grade', 'remark', 'grade_point']


class ResultTemplateForm(forms.ModelForm):
    class Meta:
        model = ResultTemplate
        fields = [
            'name', 'school_class', 'term', 'grade_scale',
            'test_max_score', 'exam_max_score',
            'calculate_class_position', 'calculate_subject_position',
            'show_percentage', 'show_grade_points', 'show_remarks',
            'is_active'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to active terms
        self.fields['term'].queryset = Term.objects.filter(is_active=True)


class StudentResultForm(forms.ModelForm):
    class Meta:
        model = StudentResult
        fields = ['test_score', 'exam_score']
        widgets = {
            'test_score': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'exam_score': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        self.class_subject = kwargs.pop('class_subject', None)
        self.student = kwargs.pop('student', None)
        self.term = kwargs.pop('term', None)
        self.result_template = kwargs.pop('result_template', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        if not self.instance.pk:
            self.instance.class_subject = self.class_subject
            self.instance.student = self.student
            self.instance.term = self.term
            self.instance.result_template = self.result_template
            self.instance.entered_by = self.initial.get('entered_by')
        return super().save(commit=commit)


class BulkResultEntryForm(forms.Form):
    """Form for bulk entering results for multiple students"""
    def __init__(self, *args, **kwargs):
        class_subjects = kwargs.pop('class_subjects', [])
        students = kwargs.pop('students', [])
        super().__init__(*args, **kwargs)

        # Create fields for each student-subject combination
        for student in students:
            for class_subject in class_subjects:
                test_field_name = f"test_{student.pk}_{class_subject.pk}"
                exam_field_name = f"exam_{student.pk}_{class_subject.pk}"

                self.fields[test_field_name] = forms.DecimalField(
                    max_digits=5, decimal_places=2, required=False,
                    widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': 'Test'})
                )
                self.fields[exam_field_name] = forms.DecimalField(
                    max_digits=5, decimal_places=2, required=False,
                    widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': 'Exam'})
                )


class AdmissionLookupForm(forms.Form):
    """Form for students to look up their results by admission number"""
    admission_no = forms.CharField(
        max_length=30,
        label="Admission Number",
        widget=forms.TextInput(attrs={'placeholder': 'Enter your admission number'})
    )


class ReportCardCommentForm(forms.ModelForm):
    """Form for teachers to add comments to report cards"""
    class Meta:
        model = ReportCardComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Add your comment about the student\'s performance and conduct',
                'class': 'form-control'
            })
        }
        labels = {
            'comment': 'Report Card Comment'
        }
