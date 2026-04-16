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
