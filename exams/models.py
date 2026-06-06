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

    name = models.CharField(max_length=20, choices=TERM_CHOICES)
    display_name = models.CharField(max_length=50, default='Term')
    academic_year = models.CharField(max_length=20, help_text="e.g., 2023/2024")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ('academic_year', 'name')

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


class ExamPaper(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned for Review'),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exam_papers')
    school_class = models.ForeignKey(SchoolClasses, on_delete=models.CASCADE, related_name='exam_papers')
    teacher = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='created_exams')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='exam_papers')
    academic_session = models.CharField(max_length=20, help_text='e.g., 2023/2024')
    duration = models.CharField(max_length=50, blank=True)
    total_marks = models.PositiveIntegerField(default=100)
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} - {self.school_class} ({self.academic_session}) [{self.get_status_display()}]"


class ExamSection(models.Model):
    SECTION_TYPES = [
        ('objective', 'Objective'),
        ('theory', 'Theory'),
        ('german', 'German Questions'),
        ('other', 'Custom / Optional'),
    ]

    exam = models.ForeignKey(ExamPaper, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=120, blank=True)
    section_type = models.CharField(max_length=30, choices=SECTION_TYPES, default='theory')
    instruction = models.TextField(blank=True)
    marks_allocation = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title or self.get_section_type_display()} ({self.exam})"


class Question(models.Model):
    QUESTION_TYPES = [
        ('objective', 'Objective'),
        ('theory', 'Theory'),
    ]

    SUBNUMBERING_STYLES = [
        ('', 'No sub-question numbering'),
        ('parent_alpha', '1(a), 1(b), 1(c)'),
        ('roman', 'i, ii, iii'),
        ('alpha', 'a, b, c'),
        ('custom', 'Custom'),
    ]

    section = models.ForeignKey(ExamSection, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    marks = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='theory')
    correct_answer = models.CharField(max_length=10, blank=True, help_text='Stored for records only')
    teacher_guide = models.TextField(blank=True)
    resource_notes = models.TextField(blank=True)
    subnumbering_style = models.CharField(max_length=20, choices=SUBNUMBERING_STYLES, blank=True, default='')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order} ({self.get_question_type_display()}) - {self.section}"


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_label = models.CharField(max_length=2)
    option_text = models.TextField(blank=True)

    class Meta:
        ordering = ['option_label']

    def __str__(self):
        return f"{self.option_label}) {self.option_text[:60]}"


class ApprovalLog(models.Model):
    ACTION_CHOICES = [
        ('submit', 'Submit'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('return', 'Return for Review'),
        ('edit', 'Edit'),
    ]

    exam = models.ForeignKey(ExamPaper, on_delete=models.CASCADE, related_name='approval_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    comment = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_action_display()} by {self.user} on {self.timestamp}"
