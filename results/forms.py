from django import forms
from .models import (
    GradeScale, ResultTemplate, StudentResult, ReportCardComment, StudentConduct
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
    """Form for bulk entering results for multiple students with conduct traits"""
    def __init__(self, *args, **kwargs):
        class_subjects = kwargs.pop('class_subjects', [])
        students = kwargs.pop('students', [])
        self.students = students
        self.class_subjects = class_subjects
        super().__init__(*args, **kwargs)

        # Create fields for each student-subject combination
        for student in students:
            # Score entry fields
            for class_subject in class_subjects:
                test_field_name = f"test_{student.pk}_{class_subject.pk}"
                exam_field_name = f"exam_{student.pk}_{class_subject.pk}"

                self.fields[test_field_name] = forms.DecimalField(
                    max_digits=5, decimal_places=2, required=False,
                    widget=forms.NumberInput(attrs={
                        'step': '0.01', 'min': '0',
                        'class': 'form-control form-control-sm score-input',
                        'data-student-id': student.pk,
                        'data-subject-id': class_subject.pk,
                        'data-type': 'test'
                    })
                )
                self.fields[exam_field_name] = forms.DecimalField(
                    max_digits=5, decimal_places=2, required=False,
                    widget=forms.NumberInput(attrs={
                        'step': '0.01', 'min': '0',
                        'class': 'form-control form-control-sm score-input',
                        'data-student-id': student.pk,
                        'data-subject-id': class_subject.pk,
                        'data-type': 'exam'
                    })
                )

            # Conduct/trait fields for each student
            attendance_field_name = f"attendance_{student.pk}"
            conduct_field_name = f"conduct_{student.pk}"
            punctuality_field_name = f"punctuality_{student.pk}"
            attentiveness_field_name = f"attentiveness_{student.pk}"
            participation_field_name = f"participation_{student.pk}"
            teacher_notes_field_name = f"teacher_notes_{student.pk}"

            self.fields[attendance_field_name] = forms.ChoiceField(
                choices=StudentConduct.ATTENDANCE_CHOICES,
                initial='Good',
                widget=forms.Select(attrs={
                    'class': 'form-select form-select-sm',
                    'data-student-id': student.pk
                })
            )
            self.fields[conduct_field_name] = forms.ChoiceField(
                choices=StudentConduct.CONDUCT_CHOICES,
                initial='Good',
                widget=forms.Select(attrs={
                    'class': 'form-select form-select-sm',
                    'data-student-id': student.pk
                })
            )
            self.fields[punctuality_field_name] = forms.ChoiceField(
                choices=StudentConduct.PUNCTUALITY_CHOICES,
                initial='Good',
                widget=forms.Select(attrs={
                    'class': 'form-select form-select-sm',
                    'data-student-id': student.pk
                })
            )
            self.fields[attentiveness_field_name] = forms.ChoiceField(
                choices=StudentConduct.CONDUCT_CHOICES,
                initial='Good',
                widget=forms.Select(attrs={
                    'class': 'form-select form-select-sm',
                    'data-student-id': student.pk
                })
            )
            self.fields[participation_field_name] = forms.ChoiceField(
                choices=StudentConduct.CONDUCT_CHOICES,
                initial='Good',
                widget=forms.Select(attrs={
                    'class': 'form-select form-select-sm',
                    'data-student-id': student.pk
                })
            )
            self.fields[teacher_notes_field_name] = forms.CharField(
                required=False,
                widget=forms.Textarea(attrs={
                    'rows': 2,
                    'class': 'form-control form-control-sm',
                    'placeholder': 'Teacher notes',
                    'data-student-id': student.pk
                })
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
