from django.contrib import admin
from .models import Student, StudentApplication, AdmissionFormField, AdmissionFormResponse


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "admission_no",
        "surname",
        "other_names",
        "student_class",
        "gender",
        "get_user_status",
    )
    list_filter = ("student_class", "gender", "user")
    search_fields = ("admission_no", "surname", "other_names", "user__username", "user__email")
    readonly_fields = ("get_user_link",)
    
    fieldsets = (
        (None, {
            'fields': (
                'admission_no', 'surname', 'other_names', 'dob', 'gender', 'student_class', 'photo', 'status', 'date_left'
            )
        }),
        ('Student Login Account', {
            'fields': ('user', 'get_user_link'),
            'description': 'Link this student to a user account to allow portal login. Student must first create an account and request the "Student" role.'
        }),
    )
    
    def get_user_status(self, obj):
        """Display whether student has a linked user account"""
        if obj.user:
            return f'✓ {obj.user.username}'
        return '✗ Not linked'
    get_user_status.short_description = 'User Account'
    
    def get_user_link(self, obj):
        """Display user details if linked"""
        if obj.user:
            return f'Linked to: {obj.user.get_full_name()} ({obj.user.username}) - Email: {obj.user.email}'
        return 'No user account linked'
    get_user_link.short_description = 'Account Details'


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


@admin.register(AdmissionFormField)
class AdmissionFormFieldAdmin(admin.ModelAdmin):
    list_display = ('label', 'field_type', 'required', 'order', 'is_active')
    list_filter = ('field_type', 'required', 'is_active')
    search_fields = ('label', 'name')
    ordering = ['order']
    fieldsets = (
        ('Field Information', {
            'fields': ('name', 'label', 'field_type', 'order')
        }),
        ('Configuration', {
            'fields': ('required', 'help_text', 'placeholder', 'choices', 'is_active'),
            'description': 'For dropdown fields, enter comma-separated choices'
        }),
    )


@admin.register(AdmissionFormResponse)
class AdmissionFormResponseAdmin(admin.ModelAdmin):
    list_display = ('application', 'field', 'value')
    list_filter = ('field', 'application__status')
    search_fields = ('application__first_name', 'application__last_name')
    readonly_fields = ('application', 'field', 'value')
