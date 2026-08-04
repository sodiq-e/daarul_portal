from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from accounts.models import Profile
from .models import PortalThread
from .views import get_or_create_group_thread_for_users, get_or_create_personal_thread_for_users


class PortalThreadTypeRegressionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pw')
        self.other_user = User.objects.create_user(username='bob', password='pw')
        self.third_user = User.objects.create_user(username='carol', password='pw')

    def test_personal_thread_reuses_existing_thread_for_same_two_participants(self):
        first = get_or_create_personal_thread_for_users([self.user, self.other_user])
        second = get_or_create_personal_thread_for_users([self.other_user, self.user])

        self.assertEqual(first.id, second.id)
        self.assertEqual(first.thread_type, PortalThread.THREAD_TYPE_PERSONAL)
        self.assertEqual(first.user_id, self.user.id)
        self.assertEqual(set(first.participants.values_list('id', flat=True)), {self.user.id, self.other_user.id})

    def test_group_thread_reuses_existing_thread_for_same_group_participants(self):
        first = get_or_create_group_thread_for_users([self.user, self.other_user, self.third_user], name='Staff Group')
        second = get_or_create_group_thread_for_users([self.third_user, self.user, self.other_user], name='Staff Group')

        self.assertEqual(first.id, second.id)
        self.assertEqual(first.thread_type, PortalThread.THREAD_TYPE_GROUP)
        self.assertEqual(first.name, 'Staff Group')
        self.assertEqual(set(first.participants.values_list('id', flat=True)), {self.user.id, self.other_user.id, self.third_user.id})


class AdminPortalThreadAccessTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='pw', is_staff=True, is_superuser=True)
        Profile.objects.get_or_create(user=self.admin, defaults={'is_approved': True})

    def test_deleted_thread_redirects_to_admin_portal_users_list(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin_portal_thread_detail', kwargs={'thread_id': 99999}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin_portal_users_list'))


class PortalPresenceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pw')
        self.other_user = User.objects.create_user(username='bob', password='pw')
        self.thread = PortalThread.objects.create()
        self.thread.participants.set([self.user, self.other_user])

    def test_sync_portal_presence_updates_server_state(self):
        self.client.force_login(self.user)
        first_response = self.client.post(
            reverse('sync_portal_presence'),
            {'thread_id': self.thread.id},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(first_response.status_code, 200)
        first_payload = first_response.json()
        self.assertTrue(first_payload['success'])
        self.assertFalse(first_payload['presence']['participant']['is_online'])
        self.assertEqual(first_payload['presence']['participant']['user_id'], self.other_user.id)

        self.client.force_login(self.other_user)
        second_response = self.client.post(
            reverse('sync_portal_presence'),
            {'thread_id': self.thread.id},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(second_response.status_code, 200)
        second_payload = second_response.json()
        self.assertTrue(second_payload['success'])
        self.assertTrue(second_payload['presence']['participant']['is_online'])
        self.assertEqual(second_payload['presence']['participant']['user_id'], self.user.id)
