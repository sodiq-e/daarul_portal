from django.contrib import admin
from .models import (
    Term, Subject, ClassSubject, ExamType, Exam
)
from .models import (
    ExamPaper, ExamSection, Question, QuestionOption, ApprovalLog
)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'academic_year', 'is_active')
    list_filter = ('is_active', 'academic_year')
    search_fields = ('name', 'display_name')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ('school_class', 'subject', 'is_compulsory', 'order')
    list_filter = ('school_class', 'is_compulsory')
    search_fields = ('school_class__class_name', 'subject__name')
    ordering = ('school_class', 'order')


@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'assessment_type', 'max_score', 'weight_percentage', 'is_active')
    list_filter = ('assessment_type', 'is_active')
    search_fields = ('name',)


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'term', 'school_class', 'exam_type', 'date', 'is_active')
    list_filter = ('term', 'school_class', 'exam_type', 'is_active')
    search_fields = ('name', 'school_class__class_name')


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 0


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


class ExamSectionInline(admin.TabularInline):
    model = ExamSection
    extra = 0


@admin.register(ExamPaper)
class ExamPaperAdmin(admin.ModelAdmin):
    list_display = ('subject', 'school_class', 'teacher', 'academic_session', 'status', 'created_at')
    list_filter = ('status', 'academic_session', 'school_class')
    search_fields = ('subject__name', 'teacher__username')
    inlines = [ExamSectionInline]


@admin.register(ExamSection)
class ExamSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'exam', 'section_type', 'marks_allocation', 'order')
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'section', 'question_type', 'marks', 'order')
    list_filter = ('question_type',)
    search_fields = ('question_text',)

    def short_text(self, obj):
        return (obj.question_text[:75] + '...') if len(obj.question_text) > 75 else obj.question_text


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ('question', 'option_label', 'short_text')

    def short_text(self, obj):
        return (obj.option_text[:75] + '...') if len(obj.option_text) > 75 else obj.option_text


@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):
    list_display = ('exam', 'action', 'user', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('exam__subject__name', 'user__username')
