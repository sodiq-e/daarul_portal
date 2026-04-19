from django.contrib import admin
from .models import SchoolClasses, Teacher, ClassTeacher, SchemeOfWork, SchemeWeek, TeacherPermission


@admin.register(SchoolClasses)
class SchoolClassesAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'level', 'description')
    search_fields = ('class_name', 'level')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'qualification', 'is_approved', 'is_active')
    list_filter = ('is_approved', 'is_active', 'qualification')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id')
    readonly_fields = ('approved_at', 'approved_by')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'approved_by')


@admin.register(ClassTeacher)
class ClassTeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'school_class', 'subject', 'is_class_teacher', 'is_active')
    list_filter = ('is_class_teacher', 'is_active', 'school_class', 'subject')
    search_fields = ('teacher__user__username', 'school_class__class_name', 'subject__name')
    autocomplete_fields = ('teacher', 'school_class', 'subject')


class SchemeWeekInline(admin.TabularInline):
    model = SchemeWeek
    extra = 0
    fields = ('week_number', 'topic', 'is_completed', 'completed_date')
    readonly_fields = ('completed_date',)


@admin.register(SchemeOfWork)
class SchemeOfWorkAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'school_class', 'subject', 'term', 'is_submitted', 'is_approved')
    list_filter = ('is_submitted', 'is_approved', 'term', 'school_class', 'subject')
    search_fields = ('title', 'teacher__user__username', 'school_class__class_name')
    readonly_fields = ('submitted_at', 'approved_at', 'approved_by')
    inlines = [SchemeWeekInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('teacher__user', 'school_class', 'subject', 'term')


@admin.register(TeacherPermission)
class TeacherPermissionAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'permission', 'is_granted', 'granted_at')
    list_filter = ('permission', 'is_granted', 'granted_at')
    search_fields = ('teacher__user__username', 'teacher__user__first_name', 'teacher__user__last_name')
    autocomplete_fields = ('teacher',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('teacher__user')
