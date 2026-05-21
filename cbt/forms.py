from django import forms
from django.forms import inlineformset_factory
from .models import CBTExam, CBTQuestion, CBTChoice


class CBTExamForm(forms.ModelForm):
    class Meta:
        model = CBTExam
        fields = [
            'name',
            'exam_mode',
            'subject',
            'school_class',
            'term',
            'linked_exam',
            'duration_minutes',
            'start_datetime',
            'end_datetime',
            'is_published',
            'is_active',
            'allow_ai_questions',
        ]
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class CBTQuestionForm(forms.ModelForm):
    class Meta:
        model = CBTQuestion
        fields = ['prompt', 'question_type', 'mark_value', 'order', 'is_active', 'explanation']
        widgets = {
            'prompt': forms.Textarea(attrs={'rows': 3}),
            'explanation': forms.Textarea(attrs={'rows': 2}),
        }


class CBTChoiceForm(forms.ModelForm):
    class Meta:
        model = CBTChoice
        fields = ['text', 'is_correct', 'order']


CBTChoiceFormSet = inlineformset_factory(
    CBTQuestion,
    CBTChoice,
    form=CBTChoiceForm,
    extra=4,
    can_delete=True,
    min_num=2,
    validate_min=True,
)
