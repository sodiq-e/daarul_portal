from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum, Avg, F
from django.utils import timezone
from students.models import Student
from exams.models import Exam, Subject, ClassSubject, Term
from school_classes.models import SchoolClasses


class GradeScale(models.Model):
    """Configurable grading system"""
    name = models.CharField(max_length=50)
    min_score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=5)
    remark = models.CharField(max_length=50)
    grade_point = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    class Meta:
        unique_together = ('name', 'grade')
        ordering = ['-min_score']

    def __str__(self):
        return f"{self.grade} ({self.min_score}-{self.max_score})"


class ResultTemplate(models.Model):
    """Configurable report card template"""
    name = models.CharField(max_length=100, unique=True)
    school_class = models.ForeignKey(
        SchoolClasses,
        on_delete=models.CASCADE,
        related_name='result_templates'
    )
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    grade_scale = models.ForeignKey(GradeScale, on_delete=models.CASCADE)

    # Score configurations
    test_max_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=40.00,
        validators=[MinValueValidator(0)]
    )
    exam_max_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=60.00,
        validators=[MinValueValidator(0)]
    )

    # Position calculation settings
    calculate_class_position = models.BooleanField(default=True)
    calculate_subject_position = models.BooleanField(default=True)

    # Additional fields
    show_percentage = models.BooleanField(default=True)
    show_grade_points = models.BooleanField(default=True)
    show_remarks = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('school_class', 'term')

    def __str__(self):
        return f"{self.school_class} - {self.term} Template"


class StudentResult(models.Model):
    """Comprehensive student result record"""
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='results'
    )
    class_subject = models.ForeignKey(
        ClassSubject,
        on_delete=models.CASCADE,
        related_name='student_results'
    )
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    result_template = models.ForeignKey(
        ResultTemplate,
        on_delete=models.CASCADE,
        related_name='student_results'
    )

    # Scores
    test_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    exam_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)]
    )

    # Calculated fields
    total_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    grade = models.CharField(max_length=5, blank=True)
    remark = models.CharField(max_length=50, blank=True)
    grade_point = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True
    )

    # Positions
    class_position = models.PositiveIntegerField(null=True, blank=True)
    subject_position = models.PositiveIntegerField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    entered_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ('student', 'class_subject', 'term')

    def save(self, *args, **kwargs):
        """Auto-calculate total, percentage, grade, and remark"""
        if self.test_score is not None and self.exam_score is not None:
            # Calculate total score
            test_weight = self.result_template.test_max_score / (self.result_template.test_max_score + self.result_template.exam_max_score)
            exam_weight = self.result_template.exam_max_score / (self.result_template.test_max_score + self.result_template.exam_max_score)

            self.total_score = (self.test_score * test_weight) + (self.exam_score * exam_weight)

            # Calculate percentage
            max_total = self.result_template.test_max_score + self.result_template.exam_max_score
            self.percentage = (self.total_score / max_total) * 100

            # Get grade from scale
            grade_scale = self.result_template.grade_scale
            matching_grade = GradeScale.objects.filter(
                name=grade_scale.name,
                min_score__lte=self.percentage,
                max_score__gte=self.percentage
            ).first()

            if matching_grade:
                self.grade = matching_grade.grade
                self.remark = matching_grade.remark
                self.grade_point = matching_grade.grade_point

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.class_subject.subject} ({self.term})"


class TermResult(models.Model):
    """Aggregated term results for a student"""
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='term_results'
    )
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    result_template = models.ForeignKey(
        ResultTemplate,
        on_delete=models.CASCADE,
        related_name='term_results'
    )

    # Aggregated scores
    total_subjects = models.PositiveIntegerField(default=0)
    total_score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    average_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overall_grade = models.CharField(max_length=5, blank=True)
    overall_remark = models.CharField(max_length=50, blank=True)

    # Positions
    class_position = models.PositiveIntegerField(null=True, blank=True)

    # Status
    is_complete = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'term')

    def calculate_aggregates(self):
        """Calculate term aggregates from individual subject results"""
        subject_results = StudentResult.objects.filter(
            student=self.student,
            term=self.term,
            result_template=self.result_template
        )

        if subject_results.exists():
            self.total_subjects = subject_results.count()
            self.total_score = subject_results.aggregate(
                total=Sum('total_score')
            )['total'] or 0

            self.average_percentage = subject_results.aggregate(
                avg=Avg('percentage')
            )['avg']

            if self.average_percentage:
                # Get overall grade
                grade_scale = self.result_template.grade_scale
                matching_grade = GradeScale.objects.filter(
                    name=grade_scale.name,
                    min_score__lte=self.average_percentage,
                    max_score__gte=self.average_percentage
                ).first()

                if matching_grade:
                    self.overall_grade = matching_grade.grade
                    self.overall_remark = matching_grade.remark

            self.is_complete = True
            self.completed_at = timezone.now()
            self.save()

    def __str__(self):
        return f"{self.student} - {self.term} Term Result"


class Promotion(models.Model):
    """Student promotions between classes"""

    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    from_class = models.ForeignKey(
        SchoolClasses,
        on_delete=models.CASCADE,
        related_name='promotions_from'
    )

    to_class = models.ForeignKey(
        SchoolClasses,
        on_delete=models.CASCADE,
        related_name='promotions_to'
    )

    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    promoted_date = models.DateField(auto_now_add=True)
    remarks = models.TextField(blank=True)

    promoted_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.student} promoted from {self.from_class} to {self.to_class}"

class ReportCardComment(models.Model):
    """Teacher comments on student report cards"""
    term_result = models.ForeignKey(
        TermResult,
        on_delete=models.CASCADE,
        related_name='teacher_comments'
    )
    teacher = models.ForeignKey(
        'school_classes.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='report_card_comments'
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_report_comments'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment for {self.term_result.student} by {self.created_by}"


class StudentConduct(models.Model):
    """Student conduct, attendance, and behavioral traits for each term"""
    
    ATTENDANCE_CHOICES = [
        ('Excellent', 'Excellent (95-100%)'),
        ('Very Good', 'Very Good (85-94%)'),
        ('Good', 'Good (75-84%)'),
        ('Fair', 'Fair (65-74%)'),
        ('Poor', 'Poor (<65%)'),
    ]
    
    CONDUCT_CHOICES = [
        ('Excellent', 'Excellent'),
        ('Very Good', 'Very Good'),
        ('Good', 'Good'),
        ('Fair', 'Fair'),
        ('Poor', 'Poor'),
    ]
    
    PUNCTUALITY_CHOICES = [
        ('Excellent', 'Always on time'),
        ('Very Good', 'Usually on time'),
        ('Good', 'Mostly on time'),
        ('Fair', 'Often late'),
        ('Poor', 'Frequently late'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='conduct_records'
    )
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    
    # Conduct traits
    attendance = models.CharField(
        max_length=20,
        choices=ATTENDANCE_CHOICES,
        default='Good',
        help_text='Student attendance rating'
    )
    conduct = models.CharField(
        max_length=20,
        choices=CONDUCT_CHOICES,
        default='Good',
        help_text='Student general conduct'
    )
    punctuality = models.CharField(
        max_length=20,
        choices=PUNCTUALITY_CHOICES,
        default='Good',
        help_text='Student punctuality'
    )
    attentiveness = models.CharField(
        max_length=20,
        choices=CONDUCT_CHOICES,
        default='Good',
        help_text='Student attentiveness in class'
    )
    participation = models.CharField(
        max_length=20,
        choices=CONDUCT_CHOICES,
        default='Good',
        help_text='Student participation in class'
    )
    
    # Notes
    teacher_notes = models.TextField(
        blank=True,
        help_text='General teacher comments about student progress'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    entered_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entered_conduct_records'
    )
    
    class Meta:
        unique_together = ('student', 'term')
        ordering = ['-term']
    
    def __str__(self):
        return f"{self.student} - {self.term} Conduct"

