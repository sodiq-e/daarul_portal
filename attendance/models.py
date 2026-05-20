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
