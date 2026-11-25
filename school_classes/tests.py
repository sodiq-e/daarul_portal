from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Profile
from settingsapp.models import Tenant
from school_classes.models import Teacher


@override_settings(ALLOWED_HOSTS=['.localhost', 'localhost'])
class TeacherApprovalTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='Teacher Approval School',
            slug='teacher-approval-school',
            hostname='teacher-approval-school.localhost',
        )
        self.admin = User.objects.create_user(
            username='teacher-approval-admin',
            password='test-password',
            is_staff=True,
        )
        admin_profile = self.admin.profile
        admin_profile.is_approved = True
        admin_profile.save()

        self.teacher_user = User.objects.create_user(
            username='new-teacher',
            password='test-password',
            is_active=False,
        )
        self.teacher = Teacher._base_manager.create(
            user=self.teacher_user,
            tenant=self.tenant,
            employee_id='TA001',
        )

    def test_approving_teacher_grants_school_membership_and_allows_login(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse('teachers:approve_teacher', kwargs={'pk': self.teacher.pk}),
            HTTP_HOST=self.tenant.hostname,
        )

        self.assertEqual(response.status_code, 302)
        membership = self.teacher_user.tenant_memberships.get(tenant=self.tenant)
        self.assertEqual(membership.role, 'teacher')
        self.assertTrue(membership.is_active)

        self.teacher_user.refresh_from_db()
        self.assertTrue(self.teacher_user.is_active)
        profile = Profile.objects.get(user=self.teacher_user)
        self.assertTrue(profile.is_approved)

        self.client.logout()
        response = self.client.post(
            reverse('login'),
            {'username': self.teacher_user.username, 'password': 'test-password'},
            HTTP_HOST=self.tenant.hostname,
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.session.get('_auth_user_id'))
