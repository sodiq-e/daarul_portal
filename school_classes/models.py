from django.db import models
from django.conf import settings
from django.utils import timezone


class SchoolClasses(models.Model):
    class_name = models.CharField(max_length=50, unique=True)
    level = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.class_name


class Teacher(models.Model):
    """Teacher profile with approval status"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile'
    )
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_joined = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    # Approval workflow
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_teachers'
    )

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"


class ClassTeacher(models.Model):
    """Assignment of teachers to classes"""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='class_assignments')
    school_class = models.ForeignKey(SchoolClasses, on_delete=models.CASCADE, related_name='teachers')
    subject = models.ForeignKey('exams.Subject', on_delete=models.CASCADE, related_name='class_teachers')
    is_class_teacher = models.BooleanField(
        default=False,
        help_text="Whether this teacher is the main class teacher for this class"
    )
    assigned_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('teacher', 'school_class', 'subject')

    def __str__(self):
        return f"{self.teacher} - {self.school_class} - {self.subject}"


class SchemeOfWork(models.Model):
    """14-week scheme of work for teachers"""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='schemes_of_work')
    school_class = models.ForeignKey(SchoolClasses, on_delete=models.CASCADE)
    subject = models.ForeignKey('exams.Subject', on_delete=models.CASCADE)
    term = models.ForeignKey('exams.Term', on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=20, help_text="e.g., 2023/2024")

    # Scheme details
    title = models.CharField(max_length=200)
    objectives = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    # Approval workflow
    is_submitted = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_schemes'
    )
    approval_notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('teacher', 'school_class', 'subject', 'term', 'academic_year')

    def __str__(self):
        return f"{self.title} - {self.teacher} ({self.term})"


class SchemeWeek(models.Model):
    """Individual weeks in a scheme of work"""
    scheme = models.ForeignKey(SchemeOfWork, on_delete=models.CASCADE, related_name='weeks')
    week_number = models.PositiveIntegerField()
    topic = models.CharField(max_length=200)
    sub_topics = models.TextField(blank=True)
    objectives = models.TextField(blank=True)
    teaching_methods = models.TextField(blank=True)
    resources = models.TextField(blank=True)
    assessment = models.TextField(blank=True)

    # Completion tracking
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    completion_notes = models.TextField(blank=True)
    
    # Admin acknowledgement workflow
    is_acknowledged = models.BooleanField(default=False, help_text="Teacher reported completion for this week")
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    is_approved = models.BooleanField(default=False, help_text="Admin acknowledged the completion")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_scheme_weeks'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('scheme', 'week_number')
        ordering = ['week_number']

    def __str__(self):
        return f"Week {self.week_number}: {self.topic}"


class TeacherPermission(models.Model):
    """Granular permissions for teachers"""

    PERMISSION_CHOICES = [
        # Student Management
        ('view_students', 'View Students'),
        ('edit_students', 'Edit Student Information'),

        # Results Management
        ('view_results', 'View Student Results'),
        ('edit_results', 'Edit Student Results'),
        ('print_results', 'Print Student Results'),
        ('print_broadsheet', 'Print Class Broadsheet'),

        # Attendance
        ('view_attendance', 'View Attendance'),
        ('mark_attendance', 'Mark Attendance'),

        # Scheme of Work
        ('create_scheme', 'Create Scheme of Work'),
        ('edit_scheme', 'Edit Scheme of Work'),
        ('submit_scheme', 'Submit Scheme for Approval'),

        # Payroll
        ('view_payroll', 'View Own Payroll'),
        ('view_payroll_dashboard', 'View Payroll Dashboard'),

        # Communication
        ('view_guardians', 'View Guardian Information'),
        ('contact_guardians', 'Contact Guardians'),
    ]

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='permissions')
    permission = models.CharField(max_length=50, choices=PERMISSION_CHOICES)
    is_granted = models.BooleanField(default=False)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_permissions'
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('teacher', 'permission')

    def __str__(self):
        return f"{self.teacher} - {self.get_permission_display()}: {'Granted' if self.is_granted else 'Denied'}"
