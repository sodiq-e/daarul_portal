from .tenant_utils import (
    bind_user_tenant_profiles,
    clear_current_tenant,
    get_current_tenant,
    resolve_tenant,
    set_current_tenant,
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
        previous_tenant = get_current_tenant()
        if request.tenant is not None:
            set_current_tenant(request.tenant)
        bind_user_tenant_profiles(getattr(request, 'user', None), request.tenant)
        try:
            return self.get_response(request)
        finally:
            if previous_tenant is not None:
                set_current_tenant(previous_tenant)
            else:
                clear_current_tenant()

    def resolve_tenant(self, request):
        return resolve_tenant(request)
