from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User

from accounts.models import Profile
from .models import PortalThread
from .services.threads import get_or_create_group_thread_for_users, get_or_create_personal_thread_for_users
from .views import (
    get_or_create_group_thread_for_users as legacy_get_or_create_group_thread_for_users,
    get_or_create_personal_thread_for_users as legacy_get_or_create_personal_thread_for_users,
    get_user_threads,
)
from settingsapp.models import Tenant
from settingsapp.tenant_utils import clear_current_tenant, set_current_tenant


class PortalThreadTypeRegressionTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Thread School', slug='thread-school', hostname='thread-school.localhost')
        set_current_tenant(self.tenant)
        self.user = User.objects.create_user(username='alice', password='pw')
        self.other_user = User.objects.create_user(username='bob', password='pw')
        self.third_user = User.objects.create_user(username='carol', password='pw')

    def tearDown(self):
        clear_current_tenant()

    def test_personal_thread_reuses_existing_thread_for_same_two_participants(self):
        first = get_or_create_personal_thread_for_users([self.user, self.other_user])
        second = get_or_create_personal_thread_for_users([self.other_user, self.user])

        self.assertEqual(first.id, second.id)
        self.assertEqual(first.thread_type, PortalThread.THREAD_TYPE_PERSONAL)
        self.assertEqual(set(first.participants.values_list('id', flat=True)), {self.user.id, self.other_user.id})

    def test_group_thread_reuses_existing_thread_for_same_group_participants(self):
        first = get_or_create_group_thread_for_users([self.user, self.other_user, self.third_user], name='Staff Group')
        second = get_or_create_group_thread_for_users([self.third_user, self.user, self.other_user], name='Staff Group')

        self.assertEqual(first.id, second.id)
        self.assertEqual(first.thread_type, PortalThread.THREAD_TYPE_GROUP)
        self.assertEqual(first.name, 'Staff Group')
        self.assertEqual(set(first.participants.values_list('id', flat=True)), {self.user.id, self.other_user.id, self.third_user.id})

    def test_service_and_legacy_thread_helpers_match_behavior(self):
        service_thread = get_or_create_personal_thread_for_users([self.user, self.other_user])
        legacy_thread = legacy_get_or_create_personal_thread_for_users([self.other_user, self.user])

        self.assertEqual(service_thread.id, legacy_thread.id)
        self.assertEqual(service_thread.thread_type, PortalThread.THREAD_TYPE_PERSONAL)
        self.assertEqual(set(service_thread.participants.values_list('id', flat=True)), {self.user.id, self.other_user.id})

    def test_user_inbox_deduplicates_duplicate_personal_threads(self):
        canonical = get_or_create_personal_thread_for_users([self.user, self.other_user])
        duplicate = PortalThread.objects.create(thread_type=PortalThread.THREAD_TYPE_PERSONAL, tenant=self.tenant)
        duplicate.participants.set([self.user, self.other_user])

        duplicate.messages.create(sender=self.user, content='Duplicate copy')
        canonical.messages.create(sender=self.user, content='Original')

        threads = list(get_user_threads(self.user, request=type('Req', (), {'tenant': self.tenant})()))

        self.assertEqual(len(threads), 1)
        self.assertEqual(set(threads[0].participants.values_list('id', flat=True)), {self.user.id, self.other_user.id})


class AdminPortalThreadAccessTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Admin Portal School', slug='admin-portal-school', hostname='admin-portal-school.localhost')
        set_current_tenant(self.tenant)
        self.admin = User.objects.create_user(username='admin', password='pw', is_staff=True, is_superuser=True)
        Profile.objects.get_or_create(user=self.admin, defaults={'is_approved': True})

    def tearDown(self):
        clear_current_tenant()

    def test_deleted_thread_redirects_to_admin_portal_users_list(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin_portal_thread_detail', kwargs={'thread_id': 99999}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin_portal_users_list'))

    def test_bulk_messages_are_saved_to_each_user_thread(self):
        target = User.objects.create_user(username='target-user', password='pw')
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('admin_portal_users_list'),
            {'selected_users': [str(target.id)], 'bulk_message': 'Hello there'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        thread = get_or_create_personal_thread_for_users([self.admin, target])
        self.assertTrue(thread.messages.filter(content='Hello there', sender=self.admin).exists())

    def test_invalid_threads_are_not_openable_and_are_hidden_from_active_lists(self):
        broken_thread = PortalThread.objects.create(thread_type=PortalThread.THREAD_TYPE_PERSONAL)
        valid_thread = PortalThread.objects.create(thread_type=PortalThread.THREAD_TYPE_PERSONAL)
        valid_thread.user = self.admin
        valid_thread.save(update_fields=['user'])
        valid_thread.participants.set([self.admin, User.objects.create_user(username='valid-user', password='pw')])

        self.assertFalse(broken_thread.is_openable)
        self.assertIn(valid_thread, PortalThread.objects.openable().all())
        self.assertNotIn(broken_thread, PortalThread.objects.openable().all())


@override_settings(ALLOWED_HOSTS=['presence-school.localhost', 'testserver'])
class PortalPresenceTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Presence School', slug='presence-school', hostname='presence-school.localhost')
        set_current_tenant(self.tenant)
        self.client.defaults['HTTP_HOST'] = 'presence-school.localhost'
        self.user = User.objects.create_user(username='alice', password='pw')
        self.other_user = User.objects.create_user(username='bob', password='pw')
        self.thread = PortalThread.objects.create()
        self.thread.participants.set([self.user, self.other_user])

    def tearDown(self):
        clear_current_tenant()

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


class PortalMessageActionTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Message School', slug='message-school', hostname='message-school.localhost')
        set_current_tenant(self.tenant)
        self.user = User.objects.create_user(username='alice', password='pw')
        self.other_user = User.objects.create_user(username='bob', password='pw')
        self.thread = PortalThread.objects.create()
        self.thread.participants.set([self.user, self.other_user])
        self.message = self.thread.messages.create(sender=self.user, content='Original message', status='sent')

    def tearDown(self):
        clear_current_tenant()

    def test_user_can_edit_own_portal_message(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('edit_portal_message_ajax', args=[self.message.id]),
            {'content': 'Updated message'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.message.refresh_from_db()
        self.assertEqual(self.message.content, 'Updated message')

    def test_user_can_delete_own_portal_message(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('delete_portal_message_ajax', args=[self.message.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertFalse(self.thread.messages.filter(pk=self.message.pk).exists())
