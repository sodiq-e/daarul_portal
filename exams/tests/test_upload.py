from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
import io


@override_settings(SECURE_SSL_REDIRECT=False, EXAM_UPLOAD_REQUIRE_APPROVED_PROFILE=False)
class UploadImageTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('uploader', password='pass')
        # ensure profile exists and approved
        from accounts.models import Profile
        Profile.objects.get_or_create(user=self.user, defaults={'is_approved': True})
        self.user.is_staff = True
        self.user.save()

    def test_upload_image_success(self):
        self.client.login(username='uploader', password='pass')
        url = reverse('exam_upload_image')
        # create a small PNG file
        png = b'\x89PNG\r\n\x1a\n' + b'0' * 100
        f = SimpleUploadedFile('test.png', png, content_type='image/png')
        resp = self.client.post(url, {'upload': f})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('url', data)
        self.assertTrue(data['url'].startswith(settings.MEDIA_URL))

    def test_upload_invalid_type(self):
        self.client.login(username='uploader', password='pass')
        url = reverse('exam_upload_image')
        f = SimpleUploadedFile('test.txt', b'hello', content_type='text/plain')
        resp = self.client.post(url, {'upload': f})
        self.assertEqual(resp.status_code, 400)

    @override_settings(EXAM_UPLOAD_MAX_SIZE=10)
    def test_upload_too_large(self):
        self.client.login(username='uploader', password='pass')
        url = reverse('exam_upload_image')
        png = b'\x89PNG\r\n\x1a\n' + b'0' * 100
        f = SimpleUploadedFile('big.png', png, content_type='image/png')
        resp = self.client.post(url, {'upload': f})
        self.assertEqual(resp.status_code, 400)

    def test_upload_unauthenticated(self):
        url = reverse('exam_upload_image')
        png = b'\x89PNG\r\n\x1a\n' + b'0' * 10
        f = SimpleUploadedFile('test.png', png, content_type='image/png')
        resp = self.client.post(url, {'upload': f})
        self.assertIn(resp.status_code, (302, 403))
