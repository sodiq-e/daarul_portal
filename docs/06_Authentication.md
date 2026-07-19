# 06. Authentication and Authorization

## Authentication Mechanism
Authentication is based on Django’s built-in auth system combined with a custom login view and a Profile model.

## Login Flow
1. User visits /login/
2. CustomLoginView validates credentials
3. The system checks whether the user exists and is active
4. The system checks whether the related Profile is approved
5. If approved, the user is logged in and redirected to home
6. If not approved, the user is denied with a message

## Password Reset Flow
- Password reset views are wired using Django auth views
- Templates for reset forms and confirmation pages are present

## Role and Access Model
The system uses:
- Django user accounts
- Profile approval state
- Group membership
- Teacher profile records
- Student profile records

## Authorization Checks Observed
- LoginRequiredMixin for authenticated-only pages
- UserPassesTestMixin with custom test_func methods
- Manual permission helpers such as user_is_staff and staff_can_manage
- TeacherPermission records used for granular teacher access

## Typical Permission Rules
- Approved users can view protected pages
- Staff/teacher/admin permissions vary by module
- Teachers can only access assigned classes when configured
- Students can access their own portal data
- Admins can access broad management views

## Approval Workflows
- Student signups require admin approval
- Teacher profiles have their own approval state
- Profile approval automatically activates the user account and adds the requested group

## Security Notes
- The application uses Django’s CSRF middleware
- The login flow intentionally blocks unapproved accounts
- Some views have defensive checks to prevent unauthorized access
