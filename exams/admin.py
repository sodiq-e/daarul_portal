from django.contrib import admin
from .models import (
    Term, Subject, ClassSubject, ExamType, Exam
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
