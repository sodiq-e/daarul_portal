from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from school_classes.models import SchoolClasses


class Student(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('transferred', 'Transferred'),
        ('graduated', 'Graduated'),
    ]
    
    admission_no = models.CharField(max_length=30, unique=True)
    surname = models.CharField(max_length=120)
    other_names = models.CharField(max_length=200, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=1,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        blank=True
    )
    student_class = models.ForeignKey(
        SchoolClasses,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students"
    )
    photo = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    date_left = models.DateField(null=True, blank=True)
    
    # Link to user account for student login
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_profile'
    )

    def full_name(self):
        return f"{self.surname} {self.other_names}".strip()

    def __str__(self):
        return f"{self.admission_no} - {self.full_name()}"


class StudentApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    admission_number_requested = models.CharField(max_length=30, blank=True)
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    other_names = models.CharField(max_length=200, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=1,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        blank=True
    )
    desired_class = models.ForeignKey(
        SchoolClasses,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications'
    )
    current_school = models.CharField(max_length=200, blank=True)
    student_address = models.TextField(blank=True)
    student_phone = models.CharField(max_length=50, blank=True)
    student_email = models.EmailField(blank=True)
    previous_school = models.CharField(max_length=200, blank=True)
    medical_information = models.TextField(blank=True)
    special_needs = models.TextField(blank=True)

    guardian_name = models.CharField(max_length=200)
    guardian_relationship = models.CharField(max_length=100, blank=True)
    guardian_phone = models.CharField(max_length=50, blank=True)
    guardian_email = models.EmailField(blank=True)
    guardian_address = models.TextField(blank=True)
    guardian_occupation = models.CharField(max_length=150, blank=True)
    guardian_employer = models.CharField(max_length=200, blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=50, blank=True)

    application_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewer_notes = models.TextField(blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_applications'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )

    class Meta:
        ordering = ['-application_date']

    def __str__(self):
        return f"{self.first_name} {self.last_name} — {self.guardian_name} ({self.status})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name} {self.other_names}".strip()

    @property
    def is_pending(self):
        return self.status == 'pending'


class AdmissionFormField(models.Model):
    """Dynamic fields for admission form that admin can customize"""
    FIELD_TYPES = [
        ('text', 'Text'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('textarea', 'Text Area'),
        ('date', 'Date'),
        ('select', 'Dropdown'),
        ('checkbox', 'Checkbox'),
        ('file', 'File Upload'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=200, help_text="Label shown on form")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='text')
    required = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    help_text = models.CharField(max_length=300, blank=True)
    placeholder = models.CharField(max_length=150, blank=True)
    choices = models.TextField(blank=True, help_text="For dropdown: comma-separated values")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.label} ({self.get_field_type_display()})"
    
    def get_choices_list(self):
        if self.choices:
            return [c.strip() for c in self.choices.split(',')]
        return []


class AdmissionFormResponse(models.Model):
    """Store responses to dynamic admission form fields"""
    application = models.ForeignKey(StudentApplication, on_delete=models.CASCADE, related_name='form_responses')
    field = models.ForeignKey(AdmissionFormField, on_delete=models.CASCADE)
    value = models.TextField()
    
    class Meta:
        unique_together = ('application', 'field')
    
    def __str__(self):
        return f"{self.application.full_name} - {self.field.label}"


class StudentPermission(models.Model):
    """Permissions for students to access specific features"""
    PERMISSION_CHOICES = [
        ('view_own_profile', 'View Own Profile'),
        ('view_own_results', 'View Own Results'),
        ('download_report_card', 'Download Report Card'),
        ('view_own_fees', 'View School Fees'),
        ('view_class_timetable', 'View Class Timetable'),
        ('view_class_announcements', 'View Class Announcements'),
        ('submit_assignments', 'Submit Assignments'),
        ('view_attendance', 'View Own Attendance'),
        ('contact_teacher', 'Contact Teachers'),
        ('access_portal', 'Access Student Portal'),
    ]
    
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='permissions')
    permission = models.CharField(max_length=50, choices=PERMISSION_CHOICES)
    is_granted = models.BooleanField(default=True, help_text="Whether this permission is granted to the student")
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_student_permissions'
    )
    notes = models.TextField(blank=True, help_text="Notes about this permission")
    
    class Meta:
        unique_together = ('student', 'permission')
        verbose_name_plural = "Student Permissions"
    
    def __str__(self):
        status = "✓" if self.is_granted else "✗"
        return f"{status} {self.student} - {self.get_permission_display()}"
    
    def get_permission_display(self):
        for code, name in self.PERMISSION_CHOICES:
            if code == self.permission:
                return name
        return self.permission
