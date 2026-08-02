from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import PortalThread


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
