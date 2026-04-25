from django.contrib import admin
from .models import (
    GradeScale, ResultTemplate, StudentResult,
    TermResult, Promotion, ReportCardComment, StudentConduct
)


@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade', 'min_score', 'max_score', 'remark', 'grade_point')
    list_filter = ('name',)
    ordering = ('name', '-min_score')


@admin.register(ResultTemplate)
class ResultTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'school_class', 'term', 'grade_scale', 'is_active')
    list_filter = ('school_class', 'term', 'is_active')
    search_fields = ('name', 'school_class__class_name')


@admin.register(StudentResult)
class StudentResultAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'get_subject', 'term', 'test_score',
        'exam_score', 'total_score', 'percentage', 'grade'
    )
    list_filter = ('term', 'class_subject__school_class', 'grade')
    search_fields = ('student__admission_no', 'student__surname')
    readonly_fields = ('total_score', 'percentage', 'grade', 'remark', 'grade_point')

    def get_subject(self, obj):
        return obj.class_subject.subject.name
    get_subject.short_description = 'Subject'


@admin.register(TermResult)
class TermResultAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'term', 'total_subjects', 'average_percentage',
        'overall_grade', 'class_position'
    )
    list_filter = ('term', 'overall_grade', 'is_complete')
    search_fields = ('student__admission_no', 'student__surname')
    readonly_fields = ('total_score', 'average_percentage', 'overall_grade')


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('student', 'from_class', 'to_class', 'term', 'promoted_date')
    list_filter = ('term', 'from_class', 'to_class')
    search_fields = ('student__admission_no', 'student__surname')


@admin.register(ReportCardComment)
class ReportCardCommentAdmin(admin.ModelAdmin):
    list_display = ('term_result', 'teacher', 'created_by', 'created_at')
    list_filter = ('created_at', 'created_by')
    search_fields = ('term_result__student__admission_no', 'comment')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(StudentConduct)
class StudentConductAdmin(admin.ModelAdmin):
    list_display = ('student', 'term', 'attendance', 'conduct', 'punctuality', 'entered_by')
    list_filter = ('term', 'attendance', 'conduct', 'punctuality')
    search_fields = ('student__admission_no', 'student__surname')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Student & Term', {
            'fields': ('student', 'term', 'entered_by')
        }),
        ('Conduct Traits', {
            'fields': ('attendance', 'conduct', 'punctuality', 'attentiveness', 'participation')
        }),
        ('Notes', {
            'fields': ('teacher_notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

