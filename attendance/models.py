from django.db import models
from django.conf import settings
from students.models import Student
from school_classes.models import SchoolClasses


class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    school_class = models.ForeignKey(SchoolClasses, on_delete=models.CASCADE)
    date = models.DateField()
    present = models.BooleanField(default=True)
    morning_present = models.BooleanField(default=True)
    afternoon_present = models.BooleanField(default=True)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendance'
    )
    marked_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('student', 'date')

    def save(self, *args, **kwargs):
        self.present = bool(self.morning_present and self.afternoon_present)
        super().save(*args, **kwargs)

    @property
    def present_sessions(self):
        return int(self.morning_present) + int(self.afternoon_present)

    @property
    def absent_sessions(self):
        return 2 - self.present_sessions

    @property
    def attendance_percentage(self):
        return round((self.present_sessions / 2) * 100, 2)

    def __str__(self):
        return f"{self.student} - {self.date} - {'P' if self.present else 'A'}"


class AttendanceSession(models.Model):
    """Track attendance sessions for classes"""
    school_class = models.ForeignKey(SchoolClasses, on_delete=models.CASCADE, related_name='attendance_sessions')
    date = models.DateField()
    teacher = models.ForeignKey(
        'school_classes.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_sessions'
    )
    total_students = models.PositiveIntegerField(default=0)
    present_count = models.PositiveIntegerField(default=0)
    absent_count = models.PositiveIntegerField(default=0)
    DAY_TYPE_CHOICES = [
        ('school_day', 'School Day'),
        ('public_holiday', 'Public Holiday'),
        ('midterm_break', 'Midterm Break'),
        ('other', 'Other'),
    ]
    day_type = models.CharField(
        max_length=20,
        choices=DAY_TYPE_CHOICES,
        default='school_day'
    )
    week_number = models.PositiveSmallIntegerField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('school_class', 'date')

    def save(self, *args, **kwargs):
        if self.date:
            self.week_number = self.date.isocalendar()[1]
        super().save(*args, **kwargs)

    @property
    def weekday(self):
        return self.date.strftime('%A') if self.date else ''

    def __str__(self):
        return f"{self.school_class} - {self.date} ({self.present_count}/{self.total_students})"


class AttendanceHoliday(models.Model):
    """School holidays and breaks"""
    HOLIDAY_TYPE_CHOICES = [
        ('public_holiday', 'Public Holiday'),
        ('school_break', 'School Break'),
        ('midterm_break', 'Midterm Break'),
        ('vacation', 'Vacation'),
        ('special_event', 'Special Event'),
    ]

    name = models.CharField(max_length=100, help_text="e.g., Christmas Holiday, Mid-term Break")
    holiday_type = models.CharField(max_length=20, choices=HOLIDAY_TYPE_CHOICES, default='public_holiday')
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField(blank=True, help_text="Optional description")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = "Attendance Holidays"

    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"

    def is_within_range(self, check_date):
        """Check if a date falls within this holiday period"""
        return self.start_date <= check_date <= self.end_date

    @property
    def duration_days(self):
        """Calculate the number of days in this holiday"""
        return (self.end_date - self.start_date).days + 1


class AttendanceSettings(models.Model):
    """Global attendance configuration"""
    # Term-related settings
    enable_term_date_restriction = models.BooleanField(
        default=True,
        help_text="Restrict attendance marking to configured term dates"
    )
    
    # Marking settings
    allow_retroactive_marking = models.BooleanField(
        default=True,
        help_text="Allow marking attendance for past dates"
    )
    
    # Minimum attendance threshold
    minimum_attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=75.00,
        help_text="Minimum attendance percentage required (0-100%)"
    )
    
    # Holiday management
    auto_mark_holidays_as_absent = models.BooleanField(
        default=False,
        help_text="Automatically mark students absent on holidays (if not explicitly marked)"
    )
    
    # Report settings
    attendance_calculation_method = models.CharField(
        max_length=20,
        choices=[
            ('days', 'By Days'),
            ('sessions', 'By Sessions (Morning/Afternoon)'),
        ],
        default='sessions',
        help_text="How to calculate attendance percentage"
    )
    
    # Notification settings
    send_low_attendance_alerts = models.BooleanField(
        default=True,
        help_text="Send notifications when student attendance drops below threshold"
    )
    
    # Session settings
    school_has_morning_session = models.BooleanField(default=True)
    school_has_afternoon_session = models.BooleanField(default=True)
    
    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_settings_updates'
    )
    
    class Meta:
        verbose_name_plural = "Attendance Settings"

    def __str__(self):
        return "School Attendance Settings"

    def save(self, *args, **kwargs):
        # Ensure only one settings record exists
        if not self.pk:
            if AttendanceSettings.objects.exists():
                # Update existing instead of creating new
                obj = AttendanceSettings.objects.first()
                self.pk = obj.pk
        super().save(*args, **kwargs)

