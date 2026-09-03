from django.core.management.base import BaseCommand

from settingsapp.management.commands.populate_tenant_data import Command as PopulateTenantDataCommand
from settingsapp.models import SchoolSettings
from settingsapp.tenant_utils import ensure_user_tenant_membership


class Command(BaseCommand):
    help = 'Create the default Daarul Bayaan tenant, bind settings to it, and backfill active user memberships.'

    def handle(self, *args, **options):
        tenant, settings = SchoolSettings.ensure_default_tenant()
        self.stdout.write(self.style.SUCCESS(f"Tenant created/updated: {tenant.name} ({tenant.slug})"))
        self.stdout.write(self.style.SUCCESS(f"Settings bound: {settings.id} -> {tenant.hostname}"))

        # Backfill existing regular user roles into the tenant.
        from django.contrib.auth import get_user_model

        User = get_user_model()
        for user in User.objects.filter(is_superuser=False):
            if hasattr(user, 'teacher_profile'):
                ensure_user_tenant_membership(user, tenant, 'teacher', is_active=True)
            elif hasattr(user, 'student_profile'):
                ensure_user_tenant_membership(user, tenant, 'student', is_active=True)
            elif hasattr(user, 'staff_profile'):
                ensure_user_tenant_membership(user, tenant, 'staff', is_active=True)
            elif user.groups.filter(name__in=['Teacher', 'Staff', 'Student', 'Parent']).exists():
                group_names = list(user.groups.filter(name__in=['Teacher', 'Staff', 'Student', 'Parent']).values_list('name', flat=True))
                for group_name in group_names:
                    role = group_name.lower()
                    if role in {'teacher', 'staff', 'student', 'parent'}:
                        ensure_user_tenant_membership(user, tenant, role, is_active=True)

        self.stdout.write(self.style.SUCCESS('Backfilled active tenant memberships for existing users.'))
