import math
import uuid
from decimal import Decimal
from datetime import date, time

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class AttendanceSettingsQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active=True)

    def current(self):
        active = self.active().order_by('-updated_at').first()
        if active:
            return active
        return self.order_by('-updated_at').first()


class StudentAttendanceSettings(models.Model):
    """Settings specific to student attendance (separate from staff settings)."""
    enable_student_attendance = models.BooleanField(
        default=True,
        help_text='Enable student attendance features in the portal.'
    )
    require_daily_checkin = models.BooleanField(
        default=False,
        help_text='Require students to check in daily via the portal/mobile app.'
    )
    allow_parent_reason_submission = models.BooleanField(
        default=True,
        help_text='Allow parents/guardians to submit reasons for absence.'
    )
    absence_threshold_warning = models.PositiveIntegerField(
        default=5,
        help_text='Number of absent days in a term before warning is triggered.'
    )
    active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Student Attendance Setting'
        verbose_name_plural = 'Student Attendance Settings'
        ordering = ['-updated_at']

    def save(self, *args, **kwargs):
        if self.active:
            StudentAttendanceSettings.objects.exclude(pk=self.pk).update(active=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_current(cls):
        current = cls.objects.filter(active=True).first()
        if current:
            return current
        # return a fallback defaults object (not saved)
        return cls(
            enable_student_attendance=True,
            require_daily_checkin=False,
            allow_parent_reason_submission=True,
            absence_threshold_warning=5,
            active=True,
        )

    def __str__(self):
        return f"Student Attendance Settings (active={self.active})"


class AttendanceSettings(models.Model):
    school_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        help_text='Latitude used for GPS validation.'
    )
    school_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        help_text='Longitude used for GPS validation.'
    )
    allowed_radius_meters = models.PositiveIntegerField(
        default=200,
        help_text='Maximum distance from school for valid clock in/out.'
    )
    normal_clock_in_time = models.TimeField(
        default=time(8, 0),
        help_text='Latest time considered on-time for clock in.'
    )
    late_after_time = models.TimeField(
        default=time(8, 30),
        help_text='Time after which clock-in is marked late.'
    )
    earliest_clock_out_time = models.TimeField(
        default=time(15, 0),
        help_text='Earliest time a teacher may clock out.'
    )
    enable_gps_verification = models.BooleanField(
        default=True,
        help_text='Require GPS verification for attendance actions.'
    )
    enable_clock_out = models.BooleanField(
        default=True,
        help_text='Allow staff to clock out after clock in.'
    )
    enable_offline_sync = models.BooleanField(
        default=True,
        help_text='Allow offline attendance records to sync automatically later.'
    )
    active = models.BooleanField(
        default=True,
        help_text='Only one active configuration is used by the system.'
    )
    updated_at = models.DateTimeField(auto_now=True)

    objects = AttendanceSettingsQuerySet.as_manager()

    class Meta:
        verbose_name = 'Attendance Setting'
        verbose_name_plural = 'Attendance Settings'
        ordering = ['-updated_at']

    def save(self, *args, **kwargs):
        if self.active:
            AttendanceSettings.objects.exclude(pk=self.pk).update(active=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_current(cls):
        current = cls.objects.filter(active=True).first()
        if current:
            return current
        fallback = cls(
            allowed_radius_meters=200,
            normal_clock_in_time=time(8, 0),
            late_after_time=time(8, 30),
            earliest_clock_out_time=time(15, 0),
            enable_gps_verification=True,
            enable_clock_out=True,
            enable_offline_sync=True,
            active=True,
        )
        return fallback

    def __str__(self):
        return f"Attendance Settings (active={self.active})"


class StaffAttendance(models.Model):
    STATUS_PRESENT = 'present'
    STATUS_LATE = 'late'
    STATUS_ABSENT = 'absent'

    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Present'),
        (STATUS_LATE, 'Late'),
        (STATUS_ABSENT, 'Absent'),
    ]

    teacher = models.ForeignKey(
        'school_classes.Teacher',
        on_delete=models.CASCADE,
        related_name='staff_attendance'
    )
    date = models.DateField(default=timezone.localdate)
    clock_in = models.DateTimeField(blank=True, null=True)
    clock_out = models.DateTimeField(blank=True, null=True)
    clock_in_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    clock_in_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    clock_out_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    clock_out_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    clock_in_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PRESENT
    )
    synced = models.BooleanField(default=False)
    sync_time = models.DateTimeField(blank=True, null=True)
    offline_sync_id = models.UUIDField(null=True, blank=True, unique=True)
    device_info = models.TextField(blank=True)
    offline_record = models.BooleanField(default=False)
    is_suspicious = models.BooleanField(default=False)
    work_duration = models.DurationField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('teacher', 'date')
        ordering = ['-date', '-clock_in']

    def clean(self):
        if self.clock_out and not self.clock_in:
            raise ValidationError('Clock out cannot be saved without an earlier clock in.')
        if self.clock_in and self.clock_out and self.clock_out < self.clock_in:
            raise ValidationError('Clock out time cannot be earlier than clock in time.')

    def save(self, *args, **kwargs):
        if self.clock_in and self.clock_out:
            duration = self.clock_out - self.clock_in
            self.work_duration = duration if duration.total_seconds() >= 0 else None
        else:
            self.work_duration = None
        super().save(*args, **kwargs)

    @property
    def formatted_work_duration(self):
        if not self.work_duration:
            return None
        total_seconds = int(self.work_duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    def __str__(self):
        return f"{self.teacher} attendance on {self.date}"


def calculate_distance_meters(lat1, lon1, lat2, lon2):
    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    except (TypeError, ValueError):
        return None

    radius = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return Decimal(radius * c)
