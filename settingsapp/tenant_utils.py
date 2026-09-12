"""
Utilities for tenant-aware queries and request handling.

This module provides tenant filtering helpers that can be used in views,
managers, and context processors to ensure data isolation across tenants.
"""
import threading
from urllib.parse import urlsplit

from django.conf import settings
from django.db.models import QuerySet, Manager
from django.core.exceptions import SuspiciousOperation

_current_tenant = threading.local()


def get_tenant_base_domain():
    """Return the configured platform domain used for tenant subdomains."""
    return str(getattr(settings, 'TENANT_BASE_DOMAIN', 'localhost.com')).lower().strip().strip('.')


def get_hostname(request):
    """Return a normalized hostname without ports or URL formatting."""
    raw_host = getattr(request, 'get_host', lambda: '')() if request is not None else ''
    return (urlsplit(f'//{raw_host}').hostname or '').lower().strip('.')


def resolve_tenant(request):
    """Resolve a tenant from an exact hostname or the configured platform domain."""
    from settingsapp.models import Tenant

    host = get_hostname(request)
    if not host:
        return None

    tenant = Tenant._base_manager.filter(hostname__iexact=host, is_active=True).first()
    if tenant:
        return tenant

    base_domain = get_tenant_base_domain()
    candidates = []
    if host.endswith(f'.{base_domain}'):
        prefix = host[:-(len(base_domain) + 1)]
        if prefix and '.' not in prefix:
            candidates.append(prefix)

    for candidate in candidates:
        if candidate != 'www':
            tenant = Tenant._base_manager.filter(slug=candidate, is_active=True).first()
            if tenant:
                return tenant
    return None


def set_current_tenant(tenant):
    """Set the active tenant for the current thread."""
    _current_tenant.value = tenant
    return tenant


def get_current_tenant():
    """Return the active tenant for the current thread, if one exists."""
    return getattr(_current_tenant, 'value', None)


def clear_current_tenant():
    """Clear the active tenant for the current thread."""
    if hasattr(_current_tenant, 'value'):
        del _current_tenant.value


def get_request_tenant(request):
    """Extract the active tenant from the request object."""
    return getattr(request, 'tenant', None) or get_current_tenant()


def bind_user_tenant_profiles(user, tenant):
    """Bind reverse profile lookups on a request user to the active tenant."""
    if user is None or tenant is None or not getattr(user, 'is_authenticated', False):
        return

    from payroll.models import Staff
    from school_classes.models import Teacher
    from students.models import Student

    profile_models = (
        ('teacher_profile', Teacher),
        ('staff_profile', Staff),
        ('student_profile', Student),
    )
    for relation_name, model in profile_models:
        relation = model._meta.get_field('user').remote_field
        profile = model._base_manager.filter(user=user, tenant=tenant).first()
        user._state.fields_cache[relation.get_accessor_name()] = profile


def normalize_tenant_roles(roles):
    """Normalize role names to the lowercase values used in the membership model."""
    if roles is None:
        return []
    if isinstance(roles, str):
        roles = [roles]
    return [str(role).strip().lower() for role in roles if str(role).strip()]


def user_has_tenant_access(user, tenant, roles=None):
    """Return true when the user has an active membership for the tenant."""
    if user is None or tenant is None:
        return False
    if getattr(user, 'is_superuser', False):
        return True

    memberships = getattr(user, 'tenant_memberships', None)
    if memberships is None:
        return False

    queryset = memberships.filter(tenant=tenant, is_active=True)
    normalized_roles = normalize_tenant_roles(roles)
    if normalized_roles:
        queryset = queryset.filter(role__in=normalized_roles)
    return queryset.exists()


def user_is_tenant_staff(user, tenant=None, roles=None):
    """Return true when the user has an active teacher/staff membership in the tenant."""
    if tenant is None:
        tenant = get_request_tenant(None)
    if tenant is None:
        return False
    if roles is None:
        roles = ['teacher', 'staff']
    return user_has_tenant_access(user, tenant, roles=roles)


def user_is_tenant_admin(user, tenant=None):
    """Return true when the user has an active school-admin membership in the tenant."""
    if tenant is None:
        tenant = get_request_tenant(None)
    return user_has_tenant_access(user, tenant, roles=['school_admin'])


def ensure_user_tenant_membership(user, tenant, role, is_active=True):
    """Create or update a tenant membership for a user and role."""
    from settingsapp.models import TenantMembership

    if user is None or tenant is None or not role:
        return None

    membership, created = TenantMembership.objects.get_or_create(
        user=user,
        tenant=tenant,
        role=role,
        defaults={'is_active': is_active},
    )
    if not created:
        membership.is_active = is_active
        membership.save(update_fields=['is_active'])
    return membership


class TenantAwareQuerySet(QuerySet):
    """QuerySet that filters by tenant from the request context."""

    def for_request(self, request):
        """Filter by the active tenant in the request."""
        tenant = get_request_tenant(request)
        if tenant is None:
            return self.none()
        return self.filter(tenant=tenant)


class TenantAwareManager(Manager):
    """Manager that automatically enforces tenant scoping for tenant models."""

    def get_queryset(self):
        tenant = get_current_tenant()
        queryset = TenantAwareQuerySet(self.model, using=self._db)
        if tenant is not None:
            return queryset.filter(tenant=tenant)
        return queryset.none()

    def for_request(self, request):
        """Filter by the active tenant in the request."""
        tenant = get_request_tenant(request)
        if tenant is None:
            return self.get_queryset()
        return self.get_queryset().filter(tenant=tenant)


def require_tenant(view_func):
    """Decorator that ensures a request has an active tenant.
    
    Raises SuspiciousOperation if no tenant is found in the request.
    Useful for views that should only be accessible via tenant subdomains.
    """
    def wrapper(request, *args, **kwargs):
        if not get_request_tenant(request):
            raise SuspiciousOperation("Tenant not found for this request")
        return view_func(request, *args, **kwargs)
    return wrapper


def get_tenant_or_403(request):
    """Get the active tenant from request or raise a 403 forbidden error."""
    from django.core.exceptions import PermissionDenied
    tenant = get_request_tenant(request)
    if not tenant:
        raise PermissionDenied("This resource is only available via a school subdomain")
    return tenant
