from django import forms
from .models import Student, StudentApplication


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['admission_no', 'surname', 'other_names', 'dob', 'gender', 'student_class', 'photo']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
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
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'student_address': forms.Textarea(attrs={'rows': 2}),
            'medical_information': forms.Textarea(attrs={'rows': 3}),
            'special_needs': forms.Textarea(attrs={'rows': 3}),
            'guardian_address': forms.Textarea(attrs={'rows': 2}),
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


class StudentApplicationReviewForm(forms.ModelForm):
    class Meta:
        model = StudentApplication
        fields = ['status', 'reviewer_notes']
        widgets = {
            'reviewer_notes': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'reviewer_notes': 'Review Notes',
        }