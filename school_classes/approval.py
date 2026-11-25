from django.contrib.auth.models import Group
from django.db import transaction
from django.utils import timezone

from accounts.models import Profile
from settingsapp.models import Tenant
from settingsapp.tenant_utils import ensure_user_tenant_membership

from .models import Teacher, TeacherPermission


@transaction.atomic
def approve_teacher_account(teacher, approved_by, tenant=None):
    tenant = teacher.tenant or tenant
    if tenant is None:
        tenant_ids = list(
            teacher.user.tenant_memberships.filter(is_active=True)
            .values_list('tenant_id', flat=True)
            .distinct()[:2]
        )
        if len(tenant_ids) == 1:
            tenant = Tenant._base_manager.filter(pk=tenant_ids[0]).first()
    if tenant is None:
        return False

    approved_at = timezone.now()
    teacher.tenant = tenant
    teacher.is_approved = True
    teacher.approved_at = approved_at
    teacher.approved_by = approved_by
    teacher.save(update_fields=['tenant', 'is_approved', 'approved_at', 'approved_by'])
    ensure_user_tenant_membership(teacher.user, tenant, 'teacher', is_active=True)

    profile, _ = Profile.objects.get_or_create(user=teacher.user)
    profile.requested_group = 'Teacher'
    profile.is_approved = True
    profile.approved_at = approved_at
    profile.approved_by = approved_by
    profile.save(update_fields=['requested_group', 'is_approved', 'approved_at', 'approved_by'])

    teacher.user.is_active = True
    teacher.user.save(update_fields=['is_active'])
    group, _ = Group.objects.get_or_create(name='Teacher')
    teacher.user.groups.add(group)

    for permission, _ in TeacherPermission.PERMISSION_CHOICES:
        TeacherPermission.objects.get_or_create(
            teacher=teacher,
            permission=permission,
            defaults={'is_granted': False},
        )
    return True
