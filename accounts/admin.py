from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from django.utils import timezone
from settingsapp.email_service import send_account_approval_email
from settingsapp.tenant_utils import get_request_tenant
from school_classes.approval import approve_teacher_account

from .models import Profile


def approve_profile_access(profile, approved_by, tenant=None):
    teacher = getattr(profile.user, 'teacher_profile', None)
    if teacher is not None:
        return approve_teacher_account(teacher, approved_by, tenant=tenant)

    if not profile.user.tenant_memberships.filter(is_active=True).exists():
        return False

    profile.is_approved = True
    profile.approved_at = timezone.now()
    profile.approved_by = approved_by
    profile.save(update_fields=['is_approved', 'approved_at', 'approved_by'])
    if not profile.user.is_active:
        profile.user.is_active = True
        profile.user.save(update_fields=['is_active'])
    return True


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class UserAdmin(DjangoUserAdmin):
    inlines = (ProfileInline,)
    list_display = DjangoUserAdmin.list_display + ('is_approved',)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        profile = getattr(form.instance, 'profile', None)
        if profile and profile.is_approved and not approve_profile_access(
            profile,
            request.user,
            tenant=get_request_tenant(request),
        ):
            messages.error(
                request,
                f'{form.instance.username} has no active school membership. Assign a school before approving the account.',
            )

    def is_approved(self, obj):
        return getattr(obj.profile, 'is_approved', False)

    is_approved.boolean = True
    is_approved.short_description = 'Approved'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'requested_group', 'is_approved', 'requested_at', 'approved_at', 'approved_by')
    list_filter = ('is_approved', 'requested_group')
    search_fields = ('user__username', 'user__email', 'requested_group')
    actions = ['approve_selected_profiles']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.is_approved and not approve_profile_access(
            obj,
            request.user,
            tenant=get_request_tenant(request),
        ):
            messages.error(
                request,
                f'{obj.user.username} has no active school membership. Assign a school before approving the account.',
            )

    @admin.action(description='Approve selected registration requests')
    def approve_selected_profiles(self, request, queryset):
        for profile in queryset:
            if not approve_profile_access(
                profile,
                request.user,
                tenant=get_request_tenant(request),
            ):
                messages.error(
                    request,
                    f'{profile.user.username} has no school assignment. Assign a school before approving the account.',
                )
                continue

            # Send approval email to user
            send_account_approval_email(
                profile.user,
                template_context={'requested_group': profile.requested_group}
            )


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
