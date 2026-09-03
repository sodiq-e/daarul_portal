"""
Defensive mixins for handling user profiles across views.
Prevents ProfileDoesNotExist errors when accessing user.profile
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect

from settingsapp.tenant_utils import get_request_tenant, user_is_tenant_staff


class ProfileRequiredMixin(UserPassesTestMixin):
    """
    Mixin that requires the user to have an approved profile.
    Returns False if user is not authenticated or profile doesn't exist.
    """
    
    def test_func(self):
        """Check if user has an approved profile"""
        if not self.request.user.is_authenticated:
            return False
        
        try:
            return self.request.user.profile.is_approved
        except AttributeError:
            # Profile doesn't exist
            return False
    
    def handle_no_permission(self):
        """Handle when test_func returns False"""
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        
        messages.error(
            self.request, 
            'Your account is not approved yet. Please wait for an administrator.'
        )
        return redirect('home')


class StaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin that requires the user to be staff/teacher with an approved profile.
    """
    
    def test_func(self):
        """Check if user is staff/teacher and approved"""
        if not self.request.user.is_authenticated:
            return False

        tenant = get_request_tenant(self.request)
        try:
            return (
                self.request.user.profile.is_approved and
                user_is_tenant_staff(self.request.user, tenant=tenant)
            )
        except AttributeError:
            # Profile doesn't exist
            return False
    
    def handle_no_permission(self):
        """Handle when test_func returns False"""
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        
        messages.error(
            self.request,
            'You do not have permission to access this resource.'
        )
        return redirect('home')


def check_user_approved(user):
    """
    Defensive utility function to check if a user is approved.
    Returns False if user is not authenticated or profile doesn't exist.
    """
    if not user or not user.is_authenticated:
        return False
    
    try:
        return user.profile.is_approved
    except AttributeError:
        return False


def check_user_staff(user):
    """
    Defensive utility function to check if a user is staff.
    Returns False if user is not authenticated or profile doesn't exist.
    """
    if not user or not user.is_authenticated:
        return False

    try:
        tenant = getattr(user, 'tenant', None)
        if tenant is None:
            return user.profile.is_approved and user.groups.filter(name__in=['Teacher', 'Staff']).exists()
        return user.profile.is_approved and user_is_tenant_staff(user, tenant=tenant)
    except AttributeError:
        return False
