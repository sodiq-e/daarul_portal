from django import forms
from .models import (
    Term, Subject, ClassSubject, ExamType, Exam, ExamPaper, ExamSection, Question, QuestionOption
)
from school_classes.models import SchoolClasses, ClassTeacher
from ckeditor.widgets import CKEditorWidget


class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ['name', 'display_name', 'academic_year', 'start_date', 'end_date', 'next_term_begins_date', 'is_active']


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


class ExamPaperForm(forms.ModelForm):
    class Meta:
        model = ExamPaper
        fields = [
            'subject', 'school_class', 'term', 'academic_session',
            'duration', 'total_marks', 'instructions'
        ]
        widgets = {
            'instructions': forms.Textarea(attrs={
                'class': 'form-control rich-editor',
                'rows': 6,
                'placeholder': 'Enter general instructions, diagrams, images, tables or math expressions here.'
            }),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        self.fields['term'].queryset = Term.objects.filter(is_active=True)
        self.fields['academic_session'].widget.attrs.update({
            'placeholder': 'e.g., 2024/2025',
            'class': 'form-control'
        })
        self.fields['duration'].widget.attrs.update({
            'placeholder': 'e.g., 1 Hour, 2 Hours',
            'class': 'form-control'
        })

        selected_class_id = None
        if self.is_bound:
            selected_class_id = self.data.get('school_class')
        elif self.instance and self.instance.pk:
            selected_class_id = getattr(self.instance.school_class, 'id', None)
        elif self.initial.get('school_class'):
            selected_class_id = self.initial.get('school_class')

        if teacher is not None:
            assigned = ClassTeacher.objects.filter(
                teacher=teacher,
                is_active=True
            )
            class_ids = list(assigned.values_list('school_class_id', flat=True).distinct())
            self.fields['school_class'].queryset = SchoolClasses.objects.filter(id__in=class_ids)
        else:
            class_ids = []

        if selected_class_id:
            self.fields['subject'].queryset = Subject.objects.filter(
                class_assignments__school_class_id=selected_class_id,
                is_active=True
            ).distinct()
        elif class_ids:
            self.fields['subject'].queryset = Subject.objects.filter(
                class_assignments__school_class_id__in=class_ids,
                is_active=True
            ).distinct()
        else:
            self.fields['subject'].queryset = Subject.objects.filter(is_active=True)


class ExamReviewForm(forms.Form):
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter review comments...'}),
        required=False,
        label='Review Comments'
    )


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


class ExamSectionForm(forms.ModelForm):
    """Form for creating and editing exam sections"""
    class Meta:
        model = ExamSection
        fields = ['title', 'section_type', 'instruction', 'marks_allocation', 'order']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Section A - Objective Questions'
            }),
            'section_type': forms.Select(attrs={'class': 'form-control'}),
            'instruction': CKEditorWidget(attrs={'class': 'form-control'}),
            'marks_allocation': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Total marks for this section'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
            }),
        }


class QuestionForm(forms.ModelForm):
    """Form for creating and editing exam questions with rich content"""
    class Meta:
        model = Question
        fields = [
            'question_text', 'marks', 'question_type', 'correct_answer',
            'teacher_guide', 'answer_explanation', 'resource_notes',
            'subnumbering_style', 'order'
        ]
        widgets = {
            'question_text': CKEditorWidget(attrs={
                'class': 'form-control',
            }),
            'teacher_guide': CKEditorWidget(attrs={
                'class': 'form-control',
            }),
            'answer_explanation': CKEditorWidget(attrs={
                'class': 'form-control',
            }),
            'resource_notes': CKEditorWidget(attrs={
                'class': 'form-control',
            }),
            'marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.25',
                'min': '0',
                'placeholder': 'e.g., 5'
            }),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'correct_answer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'For objective questions (A, B, C, D, etc.)',
            }),
            'subnumbering_style': forms.Select(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
            }),
        }


class QuestionOptionForm(forms.ModelForm):
    """Form for creating and editing multiple choice options"""
    class Meta:
        model = QuestionOption
        fields = ['option_label', 'option_text']
        widgets = {
            'option_label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'A',
                'maxlength': '2',
                'style': 'max-width: 60px;'
            }),
            'option_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter option text'
            }),
        }


class ExamApprovalForm(forms.ModelForm):
    """Form for admin approval/rejection of exam papers"""
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('return', 'Return for Review'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Approval Action'
    )

    class Meta:
        model = ExamPaper
        fields = ['approval_notes']
        widgets = {
            'approval_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter approval notes, feedback, or reasons for rejection...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['approval_notes'].label = 'Notes'


class ExamExportForm(forms.Form):
    """Form for exporting exam papers"""
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'Word (DOCX)'),
    ]
    
    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        widget=forms.RadioSelect,
        label='Export Format'
    )
    
    include_answers = forms.BooleanField(
        required=False,
        initial=False,
        label='Include teacher guide and answers'
    )
    
    include_marks = forms.BooleanField(
        required=False,
        initial=True,
        label='Include mark allocations'
    )