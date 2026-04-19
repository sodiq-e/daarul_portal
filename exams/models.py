from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from school_classes.models import SchoolClasses


class Term(models.Model):
    """Academic terms (First Term, Second Term, Third Term)"""
    TERM_CHOICES = [
        ('first', 'First Term'),
        ('second', 'Second Term'),
        ('third', 'Third Term'),
    ]

    name = models.CharField(max_length=20, choices=TERM_CHOICES, unique=True)
    display_name = models.CharField(max_length=50, default='Term')
    academic_year = models.CharField(max_length=20, help_text="e.g., 2023/2024")
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.display_name} ({self.academic_year})"


class Subject(models.Model):
    """School subjects"""
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=30, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}" if self.code else self.name


class ClassSubject(models.Model):
    """Subjects assigned to specific classes"""
    school_class = models.ForeignKey(
        SchoolClasses,
        on_delete=models.CASCADE,
        related_name='assigned_subjects'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='class_assignments'
    )
    is_compulsory = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order in report cards")

    class Meta:
        unique_together = ('school_class', 'subject')

    def __str__(self):
        return f"{self.school_class} - {self.subject}"


class ExamType(models.Model):
    """Types of assessments (Test, Exam, etc.)"""
    ASSESSMENT_CHOICES = [
        ('test', 'Test'),
        ('exam', 'Exam'),
        ('assignment', 'Assignment'),
        ('project', 'Project'),
        ('practical', 'Practical'),
    ]

    name = models.CharField(max_length=50, unique=True)
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_CHOICES)
    max_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00,
        validators=[MinValueValidator(0), MaxValueValidator(1000)]
    )
    weight_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00,
        help_text="Weight in final calculation (e.g., 40 for 40%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.weight_percentage}%)"


class Exam(models.Model):
    """Examination sessions"""
    name = models.CharField(max_length=150)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='exams')
    school_class = models.ForeignKey(
        SchoolClasses,
        on_delete=models.CASCADE,
        related_name='exams'
    )
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE)
    date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('term', 'school_class', 'exam_type')

    def __str__(self):
        return f"{self.name} - {self.school_class} ({self.term})"
