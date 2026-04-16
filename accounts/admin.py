from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class UserAdmin(DjangoUserAdmin):
    inlines = (ProfileInline,)
    list_display = DjangoUserAdmin.list_display + ('is_approved',)

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

    @admin.action(description='Approve selected registration requests')
    def approve_selected_profiles(self, request, queryset):
        for profile in queryset:
            profile.is_approved = True
            profile.approved_at = timezone.now()
            profile.approved_by = request.user
            profile.save()


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
