from django.contrib import admin
from .models import CBTExam, CBTQuestion, CBTChoice, CBTStudentAttempt, CBTAnswer


class CBTChoiceInline(admin.TabularInline):
    model = CBTChoice
    extra = 3


class CBTQuestionInline(admin.TabularInline):
    model = CBTQuestion
    extra = 1
    fields = ('prompt', 'question_type', 'mark_value', 'order', 'is_active')


@admin.register(CBTExam)
class CBTExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_mode', 'subject', 'school_class', 'duration_minutes', 'is_published', 'is_active')
    list_filter = ('exam_mode', 'is_published', 'is_active', 'subject')
    search_fields = ('name', 'subject__name')
    inlines = [CBTQuestionInline]


@admin.register(CBTQuestion)
class CBTQuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'question_type', 'order', 'mark_value', 'is_active')
    list_filter = ('question_type', 'is_active')
    search_fields = ('prompt',)
    inlines = [CBTChoiceInline]


@admin.register(CBTStudentAttempt)
class CBTStudentAttemptAdmin(admin.ModelAdmin):
    list_display = ('exam', 'student', 'session_key', 'started_at', 'completed_at', 'score', 'is_submitted', 'is_scored')
    list_filter = ('exam__exam_mode', 'is_submitted', 'is_scored')
    search_fields = ('student__username', 'session_key', 'exam__name')


@admin.register(CBTAnswer)
class CBTAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_choice', 'is_correct', 'awarded_marks')
    list_filter = ('is_correct',)
    search_fields = ('question__prompt', 'selected_choice__text')
