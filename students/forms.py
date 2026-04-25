from django import forms
from .models import Student, StudentApplication, AdmissionFormField, AdmissionFormResponse


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['admission_no', 'surname', 'other_names', 'dob', 'gender', 'student_class', 'photo']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'admission_no': forms.TextInput(attrs={'class': 'form-control'}),
            'surname': forms.TextInput(attrs={'class': 'form-control'}),
            'other_names': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'student_class': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class StudentApplicationForm(forms.ModelForm):
    class Meta:
        model = StudentApplication
        fields = [
            'admission_number_requested',
            'first_name',
            'last_name',
            'other_names',
            'dob',
            'gender',
            'desired_class',
            'current_school',
            'student_address',
            'student_phone',
            'student_email',
            'previous_school',
            'medical_information',
            'special_needs',
            'guardian_name',
            'guardian_relationship',
            'guardian_phone',
            'guardian_email',
            'guardian_address',
            'guardian_occupation',
            'guardian_employer',
            'emergency_contact_name',
            'emergency_contact_phone',
        ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'student_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'medical_information': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'special_needs': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'guardian_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'admission_number_requested': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'other_names': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'desired_class': forms.Select(attrs={'class': 'form-select'}),
            'current_school': forms.TextInput(attrs={'class': 'form-control'}),
            'student_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'student_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'previous_school': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_relationship': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'guardian_occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_employer': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'admission_number_requested': 'Requested Admission Number',
            'desired_class': 'Class Applying For',
            'current_school': 'Current/Previous School',
            'guardian_name': 'Parent / Guardian Name',
            'guardian_relationship': 'Relationship to Student',
            'guardian_phone': 'Guardian Phone',
            'guardian_email': 'Guardian Email',
            'guardian_address': 'Guardian Address',
            'guardian_occupation': 'Guardian Occupation',
            'guardian_employer': 'Guardian Employer',
            'emergency_contact_name': 'Emergency Contact Name',
            'emergency_contact_phone': 'Emergency Contact Phone',
        }


class DynamicAdmissionForm(forms.Form):
    """Form that dynamically builds fields from AdmissionFormField model"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get all active custom fields
        fields = AdmissionFormField.objects.filter(is_active=True).order_by('order')
        
        for field in fields:
            form_field = self._create_form_field(field)
            self.fields[f'custom_{field.id}'] = form_field
    
    def _create_form_field(self, field):
        """Create a Django form field from AdmissionFormField instance"""
        attrs = {'class': 'form-control'}
        
        if field.placeholder:
            attrs['placeholder'] = field.placeholder
        
        field_kwargs = {
            'required': field.required,
            'help_text': field.help_text,
            'label': field.label,
        }
        
        if field.field_type == 'text':
            return forms.CharField(**field_kwargs, widget=forms.TextInput(attrs=attrs))
        
        elif field.field_type == 'email':
            return forms.EmailField(**field_kwargs, widget=forms.EmailInput(attrs=attrs))
        
        elif field.field_type == 'phone':
            return forms.CharField(**field_kwargs, widget=forms.TextInput(attrs={**attrs, 'type': 'tel'}))
        
        elif field.field_type == 'textarea':
            return forms.CharField(**field_kwargs, widget=forms.Textarea(attrs={**attrs, 'rows': 3}))
        
        elif field.field_type == 'date':
            return forms.DateField(**field_kwargs, widget=forms.DateInput(attrs={**attrs, 'type': 'date'}))
        
        elif field.field_type == 'select':
            choices = [(c, c) for c in field.get_choices_list()]
            attrs['class'] = 'form-select'
            return forms.ChoiceField(**field_kwargs, choices=choices, widget=forms.Select(attrs=attrs))
        
        elif field.field_type == 'checkbox':
            return forms.BooleanField(**field_kwargs, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
        
        elif field.field_type == 'file':
            return forms.FileField(**field_kwargs, widget=forms.FileInput(attrs=attrs))
        
        return forms.CharField(**field_kwargs)


class StudentApplicationReviewForm(forms.ModelForm):
    class Meta:
        model = StudentApplication
        fields = ['status', 'reviewer_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'reviewer_notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
        labels = {
            'reviewer_notes': 'Review Notes',
        }