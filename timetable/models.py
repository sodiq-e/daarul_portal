from django.core.validators import MinValueValidator
from django.db import models

from exams.models import ClassSubject, Term
from school_classes.models import SchoolClasses, Teacher
from settingsapp.models import TenantModel


class TimetableTemplate(TenantModel):
    """A reusable timetable grid for one class and academic term."""

    name = models.CharField(max_length=120)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='timetable_templates')
    school_class = models.ForeignKey(
        SchoolClasses,
        on_delete=models.CASCADE,
        related_name='timetable_templates',
    )
    is_published = models.BooleanField(default=False)
    copied_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='copies',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-term__academic_year', 'term__name', 'school_class__class_name']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'term', 'school_class'],
                name='unique_timetable_per_term_class',
            ),
        ]

    def __str__(self):
        return f'{self.school_class} - {self.term}'


class TimetableDay(TenantModel):
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ]

    timetable = models.ForeignKey(TimetableTemplate, on_delete=models.CASCADE, related_name='days')
    day = models.CharField(max_length=15, choices=DAY_CHOICES)
    order = models.PositiveIntegerField(default=0)
    is_short_day = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['timetable', 'day'], name='unique_timetable_day'),
        ]

    def __str__(self):
        return self.get_day_display()


class TimetableSlot(TenantModel):
    SLOT_TYPES = [
        ('period', 'Teaching Period'),
        ('break', 'Break'),
        ('salah', 'Salah / Prayer'),
        ('assembly', 'Assembly'),
    ]

    timetable = models.ForeignKey(TimetableTemplate, on_delete=models.CASCADE, related_name='slots')
    label = models.CharField(max_length=80)
    slot_type = models.CharField(max_length=15, choices=SLOT_TYPES, default='period')
    start_time = models.TimeField()
    end_time = models.TimeField()
    order = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['timetable', 'order'], name='unique_timetable_slot_order'),
        ]

    def __str__(self):
        return f'{self.label} ({self.start_time:%I:%M %p}-{self.end_time:%I:%M %p})'


class TimetableEntry(TenantModel):
    timetable = models.ForeignKey(TimetableTemplate, on_delete=models.CASCADE, related_name='entries')
    day = models.ForeignKey(TimetableDay, on_delete=models.CASCADE, related_name='entries')
    slot = models.ForeignKey(TimetableSlot, on_delete=models.CASCADE, related_name='entries')
    class_subject = models.ForeignKey(
        ClassSubject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timetable_entries',
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timetable_entries',
    )
    note = models.CharField(max_length=120, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['timetable', 'day', 'slot'], name='unique_timetable_entry'),
        ]

    def __str__(self):
        return f'{self.timetable} - {self.day} - {self.slot}'
