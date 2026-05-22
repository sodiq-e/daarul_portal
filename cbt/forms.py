from django import forms
from django.forms import inlineformset_factory
from .models import CBTExam, CBTQuestion, CBTChoice, QuestionBank


class QuestionBankForm(forms.ModelForm):
    class Meta:
        model = QuestionBank
        fields = ['name', 'subject', 'school_class', 'term', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter question bank name'
            }),
            'subject': forms.Select(attrs={
                'class': 'form-control'
            }),
            'school_class': forms.Select(attrs={
                'class': 'form-control'
            }),
            'term': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter description (optional)'
            }),
        }


class CBTExamForm(forms.ModelForm):
    class Meta:
        model = CBTExam
        fields = [
            'name',
            'exam_mode',
            'question_mode',
            'question_bank',
            'subject',
            'school_class',
            'term',
            'linked_exam',
            'duration_minutes',
            'start_datetime',
            'end_datetime',
            'randomize_questions',
            'randomize_answers',
            'allow_navigation',
            'one_at_a_time',
            'show_instant_results',
            'show_corrections',
            'allow_review',
            'total_questions_to_display',
            'balance_by_difficulty',
            'balance_by_topic',
            'is_published',
            'is_active',
            'allow_ai_questions',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter exam name'
            }),
            'exam_mode': forms.Select(attrs={'class': 'form-control'}),
            'question_mode': forms.Select(attrs={'class': 'form-control'}),
            'question_bank': forms.Select(attrs={
                'class': 'form-control'
            }),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'school_class': forms.Select(attrs={'class': 'form-control'}),
            'term': forms.Select(attrs={'class': 'form-control'}),
            'linked_exam': forms.Select(attrs={'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'start_datetime': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'end_datetime': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'total_questions_to_display': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'randomize_questions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'randomize_answers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_navigation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'one_at_a_time': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_instant_results': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_corrections': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_review': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'balance_by_difficulty': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'balance_by_topic': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_ai_questions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CBTQuestionForm(forms.ModelForm):
    class Meta:
        model = CBTQuestion
        fields = ['prompt', 'question_type', 'mark_value', 'topic', 'difficulty', 'explanation', 'order', 'is_active']
        widgets = {
            'prompt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter the question text'
            }),
            'question_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'mark_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'topic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter topic (e.g., Algebra, Biology)'
            }),
            'difficulty': forms.Select(attrs={
                'class': 'form-control'
            }),
            'explanation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter explanation (optional)'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class CBTChoiceForm(forms.ModelForm):
    class Meta:
        model = CBTChoice
        fields = ['text', 'is_correct', 'order']
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter choice text'
            }),
            'is_correct': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
        }


CBTChoiceFormSet = inlineformset_factory(
    CBTQuestion,
    CBTChoice,
    form=CBTChoiceForm,
    extra=4,
    can_delete=True,
    min_num=2,
    validate_min=True,
)
