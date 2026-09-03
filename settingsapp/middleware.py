from .tenant_utils import (
    bind_user_tenant_profiles,
    clear_current_tenant,
    resolve_tenant,
    set_current_tenant,
    set_tenant_script_prefix,
)


class TenantMiddleware:
    """Attach the active tenant to each request based on the current hostname.

    This is host-agnostic: it works for localhost, custom domains, and subdomains.
    The platform root domain is treated as the admin environment when no tenant matches.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = self.resolve_tenant(request)
        set_current_tenant(request.tenant)
        set_tenant_script_prefix(request, request.tenant)
        bind_user_tenant_profiles(getattr(request, 'user', None), request.tenant)
        try:
            return self.get_response(request)
        finally:
            clear_current_tenant()
            set_tenant_script_prefix(request, None)

    def resolve_tenant(self, request):
        return resolve_tenant(request)
