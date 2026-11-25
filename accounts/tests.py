from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Profile
from school_classes.models import Teacher
from settingsapp.models import Tenant, TenantMembership


@override_settings(ALLOWED_HOSTS=['.localhost', 'localhost', 'testserver'])
class DjangoTeacherApprovalTests(TestCase):
    def test_profile_admin_approval_assigns_teacher_to_school(self):
        tenant = Tenant.objects.create(
            name='Admin Approval School',
            slug='admin-approval-school',
            hostname='admin-approval-school.localhost',
        )
        admin_user = User.objects.create_superuser(
            username='platform-admin',
            email='platform-admin@example.com',
            password='test-password',
        )
        teacher_user = User.objects.create_user(
            username='admin-approved-teacher',
            email='teacher@example.com',
            password='test-password',
            is_active=False,
        )
        profile = Profile.objects.get(user=teacher_user)
        teacher = Teacher._base_manager.create(
            user=teacher_user,
            tenant=tenant,
            employee_id='AA001',
        )
        self.client.force_login(admin_user)

        with patch('accounts.admin.send_account_approval_email'):
            response = self.client.post(
                reverse('admin:accounts_profile_changelist'),
                {
                    'action': 'approve_selected_profiles',
                    '_selected_action': [str(profile.pk)],
                    'index': '0',
                    'select_across': '0',
                },
            )

        self.assertEqual(response.status_code, 302)
        teacher.refresh_from_db()
        teacher_user.refresh_from_db()
        profile.refresh_from_db()
        self.assertEqual(teacher.tenant, tenant)
        self.assertTrue(teacher.is_approved)
        self.assertTrue(teacher_user.is_active)
        self.assertTrue(profile.is_approved)
        self.assertTrue(
            TenantMembership.objects.filter(
                user=teacher_user,
                tenant=tenant,
                role='teacher',
                is_active=True,
            ).exists()
        )

        self.client.logout()
        response = self.client.post(
            reverse('login'),
            {'username': teacher_user.username, 'password': 'test-password'},
            HTTP_HOST=tenant.hostname,
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.session.get('_auth_user_id'))
