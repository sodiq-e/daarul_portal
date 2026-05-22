import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
import hashlib
import json


class QuestionBank(models.Model):
    """Independent question storage for reuse across exams"""
    name = models.CharField(max_length=180)
    subject = models.ForeignKey('exams.Subject', on_delete=models.PROTECT, related_name='cbt_question_banks')
    school_class = models.ForeignKey(
        'school_classes.SchoolClasses',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cbt_question_banks'
    )
    term = models.ForeignKey('exams.Term', on_delete=models.SET_NULL, null=True, blank=True, related_name='cbt_question_banks')
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_question_banks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', 'name']
        verbose_name = 'Question Bank'
        verbose_name_plural = 'Question Banks'

    def __str__(self):
        return f"{self.name} ({self.subject.name})"

    def get_question_count(self):
        return self.questions.filter(is_active=True).count()


class CBTExam(models.Model):
    REAL = 'real'
    PRACTICE = 'practice'
    EXAM_MODE_CHOICES = [
        (REAL, 'Real Exam'),
        (PRACTICE, 'Practice / Test'),
    ]

    QUESTION_MODE_MANUAL = 'manual'
    QUESTION_MODE_RANDOM = 'random'
    QUESTION_MODE_CHOICES = [
        (QUESTION_MODE_MANUAL, 'Manual Selection'),
        (QUESTION_MODE_RANDOM, 'Random Selection'),
    ]

    name = models.CharField(max_length=180)
    exam_mode = models.CharField(max_length=16, choices=EXAM_MODE_CHOICES, default=PRACTICE)
    question_mode = models.CharField(max_length=16, choices=QUESTION_MODE_CHOICES, default=QUESTION_MODE_MANUAL)
    randomize_questions = models.BooleanField(default=False)
    randomize_answers = models.BooleanField(default=False)
    allow_navigation = models.BooleanField(default=True)
    one_at_a_time = models.BooleanField(default=False)
    show_instant_results = models.BooleanField(default=False)
    show_corrections = models.BooleanField(default=False)
    allow_review = models.BooleanField(default=True)
    total_questions_to_display = models.PositiveIntegerField(null=True, blank=True)
    balance_by_difficulty = models.BooleanField(default=False)
    balance_by_topic = models.BooleanField(default=False)
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.SET_NULL, null=True, blank=True, related_name='exams')
    subject = models.ForeignKey('exams.Subject', on_delete=models.PROTECT, related_name='cbt_exams')
    school_class = models.ForeignKey(
        'school_classes.SchoolClasses',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cbt_exams'
    )
    term = models.ForeignKey('exams.Term', on_delete=models.SET_NULL, null=True, blank=True, related_name='cbt_exams')
    linked_exam = models.ForeignKey('exams.Exam', on_delete=models.SET_NULL, null=True, blank=True, related_name='cbt_cbt_exams')
    duration_minutes = models.PositiveIntegerField(default=60)
    start_datetime = models.DateTimeField(null=True, blank=True)
    end_datetime = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    allow_ai_questions = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_cbt_exams')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', 'name']
        verbose_name = 'CBT Exam'
        verbose_name_plural = 'CBT Exams'

    def __str__(self):
        return f"{self.name} ({self.get_exam_mode_display()})"

    def is_real_exam(self):
        return self.exam_mode == self.REAL

    def is_practice_exam(self):
        return self.exam_mode == self.PRACTICE

    def is_available(self):
        if not self.is_active or not self.is_published:
            return False
        now = timezone.now()
        if self.start_datetime and now < self.start_datetime:
            return False
        if self.end_datetime and now > self.end_datetime:
            return False
        return True


class CBTQuestion(models.Model):
    MCQ = 'mcq'
    TRUE_FALSE = 'true_false'
    SHORT_ANSWER = 'short_answer'
    QUESTION_TYPE_CHOICES = [
        (MCQ, 'Multiple Choice'),
        (TRUE_FALSE, 'True / False'),
        (SHORT_ANSWER, 'Short Answer'),
    ]

    DIFFICULTY_EASY = 'easy'
    DIFFICULTY_MEDIUM = 'medium'
    DIFFICULTY_HARD = 'hard'
    DIFFICULTY_CHOICES = [
        (DIFFICULTY_EASY, 'Easy'),
        (DIFFICULTY_MEDIUM, 'Medium'),
        (DIFFICULTY_HARD, 'Hard'),
    ]

    exam = models.ForeignKey(CBTExam, on_delete=models.CASCADE, related_name='questions')
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions')
    prompt = models.TextField()
    question_type = models.CharField(max_length=32, choices=QUESTION_TYPE_CHOICES, default=MCQ)
    mark_value = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    explanation = models.TextField(blank=True)
    topic = models.CharField(max_length=100, blank=True, db_index=True)
    difficulty = models.CharField(max_length=16, choices=DIFFICULTY_CHOICES, default=DIFFICULTY_MEDIUM)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.exam.name} - Question {self.order + 1}"


class CBTChoice(models.Model):
    question = models.ForeignKey(CBTQuestion, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=512)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text


class CBTStudentAttempt(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    exam = models.ForeignKey(CBTExam, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='cbt_attempts')
    session_key = models.CharField(max_length=64, blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_saved_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_submitted = models.BooleanField(default=False)
    score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    is_scored = models.BooleanField(default=False)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        identifier = self.student.username if self.student else self.session_key or str(self.uuid)
        return f"{self.exam.name} attempt by {identifier}"

    def is_real_attempt(self):
        return self.exam.is_real_exam()

    def is_practice_attempt(self):
        return self.exam.is_practice_exam()


class CBTAnswer(models.Model):
    attempt = models.ForeignKey(CBTStudentAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(CBTQuestion, on_delete=models.CASCADE, related_name='answers')
    selected_choice = models.ForeignKey(CBTChoice, on_delete=models.SET_NULL, null=True, blank=True)
    text_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)
    awarded_marks = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('attempt', 'question')

    def __str__(self):
        return f"Answer for {self.question}"


class StudentAttemptQuestion(models.Model):
    """Track randomized question order and options for each student attempt"""
    attempt = models.ForeignKey(CBTStudentAttempt, on_delete=models.CASCADE, related_name='attempt_questions')
    question = models.ForeignKey(CBTQuestion, on_delete=models.CASCADE)
    randomized_position = models.PositiveIntegerField()
    randomized_choice_order = models.TextField(blank=True)  # JSON array of choice IDs in randomized order
    is_answered = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('attempt', 'question')
        ordering = ['randomized_position']

    def __str__(self):
        return f"Attempt {self.attempt.uuid} - Question {self.randomized_position}"

    def get_randomized_choices(self):
        """Return choices in randomized order"""
        if not self.randomized_choice_order:
            return list(self.question.choices.all().order_by('order'))
        try:
            choice_ids = json.loads(self.randomized_choice_order)
            choices_dict = {c.id: c for c in self.question.choices.all()}
            return [choices_dict[cid] for cid in choice_ids if cid in choices_dict]
        except (json.JSONDecodeError, KeyError):
            return list(self.question.choices.all().order_by('order'))
