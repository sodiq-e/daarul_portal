# Daarul Portal - PythonAnywhere Deployment Issues & Fixes

## Issues Detected & Fixed

### 1. **Missing User Profiles** ✓ FIXED
**Issue**: User `prep1` existed without a Profile record, causing `Profile.DoesNotExist` errors when accessing `user.profile`
**Impact**: Any authenticated user without a profile would cause 500 errors
**Solution**: Created `fix_missing_profiles.py` script that creates missing profiles for all users
**Status**: ✓ Verified - 1 missing profile created

### 2. **Unsafe Profile Access in Views** ✓ FIXED
**Issue**: Multiple views accessed `self.request.user.profile.is_approved` directly in `test_func()` without checking if profile exists:
- `exams/views.py` - SubjectListView, ExamListView, etc.
- `attendance/views.py` - AttendanceRecordListView, etc.
- `school_classes/views.py` - ClassListView
- `students/views.py` - StudentListView, StudentDetailView
- `results/views.py` - results_home, report_card functions

**Impact**: If a user was authenticated but profile was inaccessible, views would crash with AttributeError
**Solution**: Added defensive helper functions:
  - `user_profile_approved(user)` - Safely checks profile.is_approved
  - `user_is_staff(user)` - Safely checks if user is staff
- Updated all test_func() methods to use these helpers
- Added try-except blocks to catch AttributeError

### 3. **Context Processor Failures** ✓ FIXED
**Issue**: Context processors run on EVERY request (including login page after logout)
- `settingsapp/context_processors.py` - school_settings() could fail on database access
- `settingsapp/context_processors.py` - announcements_context() had bare `except:` clause

**Impact**: If context processor crashed before view's dispatch, user would see 500 error before login redirect
**Solution**: Wrapped context processors in try-except blocks with fallback defaults:
  - school_settings() returns safe default theme if any error occurs
  - announcements_context() logs errors but returns empty announcements
  - Improved error logging for debugging

### 4. **Production Security Settings** ✓ FIXED
**Issue**: 
- `DEBUG=True` in .env (should be False for production)
- Weak SECRET_KEY (only 23 chars, must be at least 50 chars for production)
- Missing SECURE_HSTS_SECONDS setting

**Impact**: Application vulnerable to attacks on PythonAnywhere
**Solution**: 
  - Updated .env: `DEBUG=False`
  - Updated .env: SECRET_KEY placeholder (user must generate a secure one)
  - Updated .env: ALLOWED_HOSTS to PythonAnywhere format
  - Updated settings.py: Added SECURE_HSTS_SECONDS, SECURE_HSTS_INCLUDE_SUBDOMAINS, SECURE_HSTS_PRELOAD

### 5. **Defensive Error Handling Functions** ✓ ADDED
**New helper functions created**:

#### `accounts/profile_mixins.py` (New file)
- `ProfileRequiredMixin` - Mixin for requiring approved profiles
- `StaffRequiredMixin` - Mixin for requiring staff/teacher access
- `check_user_approved(user)` - Utility function
- `check_user_staff(user)` - Utility function

#### Helper functions in existing views:
All apps now have `user_profile_approved()` and `user_is_staff()` helpers

### 6. **Static Files** ✓ VERIFIED
**Status**: ✓ collectstatic runs successfully (warning about duplicate admin files is normal)

### 7. **Database Migrations** ✓ VERIFIED
**Status**: ✓ All migrations applied successfully

## Tests Performed

✓ Django system checks pass
✓ Database migrations verified
✓ Missing profiles created
✓ Static files collected
✓ No import errors
✓ All context processors gracefully handle errors
✓ All views safely handle missing profiles

## Files Modified

1. `daarul_portal/.env` - Updated DEBUG and SECRET_KEY settings
2. `daarul_portal/settings.py` - Added HSTS security headers
3. `settingsapp/context_processors.py` - Added comprehensive error handling
4. `exams/views.py` - Added helper functions and safe profile checks
5. `attendance/views.py` - Added helper functions and safe profile checks
6. `school_classes/views.py` - Added helper functions and safe profile checks
7. `students/views.py` - Added helper functions and safe profile checks
8. `results/views.py` - Added helper functions and safe profile checks
9. `payroll/views.py` - Enhanced staff_can_manage() with error handling
10. `accounts/profile_mixins.py` - NEW FILE with defensive mixins

## Files Created

1. `fix_missing_profiles.py` - Script to create missing user profiles
2. `accounts/profile_mixins.py` - Reusable profile checking mixins

## Recommendations for PythonAnywhere Deployment

1. **Update .env file** on PythonAnywhere with:
   - Generate a secure SECRET_KEY using: `python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - Set `ALLOWED_HOSTS=your-username.pythonanywhere.com,www.yourdomain.com`
   - Set appropriate EMAIL settings for password reset

2. **Run migrations on PythonAnywhere**:
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

3. **Run profile Fix Script**:
   ```bash
   python fix_missing_profiles.py
   ```

4. **Check logs** after deployment:
   Visit Web tab → Log files → Check error log if any issues

## Summary of "Logout → Finance" Error

**Root Cause**: Context processors were running on all requests, including for unauthenticated users. If they failed, the 500 error would occur before the view's LoginRequiredMixin could redirect to login.

**Fix**: Added comprehensive error handling to context processors with safe fallbacks, ensuring they never crash even if database access fails.
