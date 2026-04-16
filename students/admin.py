from django.contrib import admin
from .models import Student, StudentApplication


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "admission_no",
        "surname",
        "other_names",
        "student_class",
        "gender",
    )
    list_filter = ("student_class", "gender")
    search_fields = ("admission_no", "surname", "other_names")


@admin.register(StudentApplication)
class StudentApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "guardian_name",
        "desired_class",
        "status",
        "application_date",
    )
    list_filter = ("status", "desired_class", "gender")
    search_fields = ("first_name", "last_name", "guardian_name", "student_phone", "student_email")
    readonly_fields = ("application_date", "submitted_by", "reviewed_by")
    fieldsets = (
        (None, {
            'fields': (
                'admission_number_requested', 'first_name', 'last_name', 'other_names', 'dob', 'gender', 'desired_class',
                'current_school', 'previous_school', 'student_address', 'student_phone', 'student_email',
                'medical_information', 'special_needs',
            )
        }),
        ('Guardian / Contact', {
            'fields': (
                'guardian_name', 'guardian_relationship', 'guardian_phone', 'guardian_email',
                'guardian_address', 'guardian_occupation', 'guardian_employer',
                'emergency_contact_name', 'emergency_contact_phone',
            )
        }),
        ('Review', {
            'fields': ('status', 'reviewer_notes', 'submitted_by', 'reviewed_by', 'application_date'),
        }),
    )
