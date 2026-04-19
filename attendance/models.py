from django.db import models
from django.conf import settings
from students.models import Student
from school_classes.models import SchoolClasses


class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    school_class = models.ForeignKey(SchoolClasses, on_delete=models.CASCADE)
    date = models.DateField()
    present = models.BooleanField(default=True)
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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('school_class', 'date')

    def __str__(self):
        return f"{self.school_class} - {self.date} ({self.present_count}/{self.total_students})"
