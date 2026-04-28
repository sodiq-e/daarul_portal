from django import forms
from django.contrib.auth.models import User
from .models import Teacher, ClassTeacher, SchemeOfWork, SchemeWeek, TeacherPermission


class TeacherProfileForm(forms.ModelForm):
    """Form for teachers to update their profile"""

    class Meta:
        model = Teacher
        fields = [
            'employee_id', 'qualification', 'specialization',
            'phone', 'address'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class TeacherApplicationForm(forms.ModelForm):
    """Form for teacher registration"""

    # User fields
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Teacher
        fields = [
            'qualification', 'specialization', 'phone', 'address'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        # Create user first
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            is_active=False  # Will be activated upon approval
        )

        # Create teacher profile
        teacher = super().save(commit=False)
        teacher.user = user
        if commit:
            teacher.save()

        return teacher


class ClassTeacherForm(forms.ModelForm):
    """Form for assigning teachers to classes"""

    class Meta:
        model = ClassTeacher
        fields = ['teacher', 'school_class', 'subject', 'is_class_teacher']
        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-select form-control'}),
            'school_class': forms.Select(attrs={'class': 'form-select form-control'}),
            'subject': forms.Select(attrs={'class': 'form-select form-control'}),
            'is_class_teacher': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SchemeOfWorkForm(forms.ModelForm):
    """Form for creating scheme of work"""

    class Meta:
        model = SchemeOfWork
        fields = [
            'title', 'objectives', 'academic_year'
        ]
        widgets = {
            'objectives': forms.Textarea(attrs={'rows': 4}),
        }


class SchemeWeekForm(forms.ModelForm):
    """Form for scheme week details"""

    class Meta:
        model = SchemeWeek
        fields = [
            'topic', 'sub_topics', 'objectives', 'teaching_methods',
            'resources', 'assessment'
        ]
        widgets = {
            'sub_topics': forms.Textarea(attrs={'rows': 2}),
            'objectives': forms.Textarea(attrs={'rows': 2}),
            'teaching_methods': forms.Textarea(attrs={'rows': 2}),
            'resources': forms.Textarea(attrs={'rows': 2}),
            'assessment': forms.Textarea(attrs={'rows': 2}),
        }


class TeacherPermissionForm(forms.ModelForm):
    """Form for managing teacher permissions"""

    class Meta:
        model = TeacherPermission
        fields = ['permission', 'is_granted']
        widgets = {
            'permission': forms.Select(attrs={'class': 'form-select'}),
        }


class BulkTeacherPermissionForm(forms.Form):
    """Form for bulk permission assignment"""

    teachers = forms.ModelMultipleChoiceField(
        queryset=Teacher.objects.filter(is_approved=True),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    permissions = forms.MultipleChoiceField(
        choices=TeacherPermission.PERMISSION_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    is_granted = forms.BooleanField(
        required=False,
        help_text="Check to grant permissions, uncheck to revoke"
    )