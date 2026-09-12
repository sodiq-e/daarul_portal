from django import forms

from exams.models import Term
from school_classes.models import SchoolClasses
from .models import TimetableSlot, TimetableTemplate


class TimetableTemplateForm(forms.ModelForm):
    class Meta:
        model = TimetableTemplate
        fields = ['name', 'term', 'school_class', 'is_published']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Basic 1 Weekly Timetable'}),
            'term': forms.Select(attrs={'class': 'form-select'}),
            'school_class': forms.Select(attrs={'class': 'form-select'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['term'].queryset = Term.objects.order_by('-academic_year', 'name')
        self.fields['school_class'].queryset = SchoolClasses.objects.order_by('class_name')


class TimetableSlotForm(forms.ModelForm):
    class Meta:
        model = TimetableSlot
        fields = ['label', 'slot_type', 'start_time', 'end_time', 'order']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'slot_type': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(format='%H:%M', attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(format='%H:%M', attrs={'class': 'form-control', 'type': 'time'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
