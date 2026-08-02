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
        self.client.force_login(self.other_user)
        response = self.client.post(
            reverse('sync_portal_presence'),
            {'thread_id': self.thread.id},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertTrue(payload['presence']['participant']['is_online'])
        self.assertEqual(payload['presence']['participant']['user_id'], self.user.id)

        self.client.force_login(self.user)
        response = self.client.post(
            reverse('sync_portal_presence'),
            {'thread_id': self.thread.id},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertTrue(payload['presence']['participant']['is_online'])
        self.assertEqual(payload['presence']['participant']['user_id'], self.other_user.id)
