from django.contrib import admin
from .models import CBTExam, CBTQuestion, CBTChoice, CBTStudentAttempt, CBTAnswer, QuestionBank, StudentAttemptQuestion


class CBTChoiceInline(admin.TabularInline):
    model = CBTChoice
    extra = 3


class CBTQuestionInline(admin.TabularInline):
    model = CBTQuestion
    extra = 1
    fields = ('prompt', 'question_type', 'mark_value', 'order', 'is_active', 'topic', 'difficulty')


class QuestionBankQuestionInline(admin.TabularInline):
    model = CBTQuestion
    extra = 1
    fields = ('prompt', 'question_type', 'mark_value', 'topic', 'difficulty', 'is_active')


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'school_class', 'term', 'get_question_count', 'created_by', 'created_at')
    list_filter = ('subject', 'school_class', 'term', 'created_at')
    search_fields = ('name', 'description', 'subject__name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [QuestionBankQuestionInline]

    def get_question_count(self, obj):
        return obj.get_question_count()
    get_question_count.short_description = 'Questions'


@admin.register(CBTExam)
class CBTExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_mode', 'question_mode', 'subject', 'school_class', 'duration_minutes', 'is_published', 'is_active')
    list_filter = ('exam_mode', 'question_mode', 'is_published', 'is_active', 'subject', 'randomize_questions', 'randomize_answers')
    search_fields = ('name', 'subject__name')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'exam_mode', 'subject', 'school_class', 'term', 'linked_exam', 'created_by')
        }),
        ('Question Configuration', {
            'fields': ('question_mode', 'question_bank', 'total_questions_to_display', 'balance_by_difficulty', 'balance_by_topic')
        }),
        ('Randomization Settings', {
            'fields': ('randomize_questions', 'randomize_answers')
        }),
        ('Exam Behavior', {
            'fields': ('allow_navigation', 'one_at_a_time', 'show_instant_results', 'show_corrections', 'allow_review')
        }),
        ('Timing & Status', {
            'fields': ('duration_minutes', 'start_datetime', 'end_datetime', 'is_published', 'is_active', 'allow_ai_questions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CBTQuestionInline]


@admin.register(CBTQuestion)
class CBTQuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'question_type', 'difficulty', 'topic', 'order', 'mark_value', 'is_active')
    list_filter = ('question_type', 'difficulty', 'is_active', 'exam__subject')
    search_fields = ('prompt', 'topic')
    fieldsets = (
        ('Question Content', {
            'fields': ('exam', 'question_bank', 'prompt', 'explanation')
        }),
        ('Question Settings', {
            'fields': ('question_type', 'mark_value', 'order', 'is_active')
        }),
        ('Categorization', {
            'fields': ('topic', 'difficulty')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ('created_at',)
    inlines = [CBTChoiceInline]


@admin.register(CBTStudentAttempt)
class CBTStudentAttemptAdmin(admin.ModelAdmin):
    list_display = ('exam', 'student', 'session_key', 'started_at', 'completed_at', 'score', 'is_submitted', 'is_scored')
    list_filter = ('exam__exam_mode', 'is_submitted', 'is_scored', 'started_at')
    search_fields = ('student__username', 'session_key', 'exam__name')
    readonly_fields = ('uuid', 'started_at', 'last_saved_at', 'completed_at')


@admin.register(CBTAnswer)
class CBTAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_choice', 'is_correct', 'awarded_marks')
    list_filter = ('is_correct', 'updated_at')
    search_fields = ('question__prompt', 'selected_choice__text')
    readonly_fields = ('updated_at',)


@admin.register(StudentAttemptQuestion)
class StudentAttemptQuestionAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'randomized_position', 'is_answered', 'is_flagged')
    list_filter = ('is_answered', 'is_flagged', 'created_at')
    search_fields = ('attempt__uuid', 'question__prompt')
    readonly_fields = ('created_at',)
