from io import BytesIO
import tempfile

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from accounts.models import Profile
from school_classes.models import SchoolClasses
from settingsapp.models import Tenant, TenantMembership
from settingsapp.tenant_utils import clear_current_tenant, set_current_tenant
from students.models import Student, StudentApplication


class StudentPhotoUploadTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        self.override_media = self.settings(MEDIA_ROOT=self.media_dir.name)
        self.override_media.enable()
        self.addCleanup(self.override_media.disable)

        self.tenant = Tenant.objects.create(
            name='Photo School',
            slug='photo-school',
            hostname='photo-school.localhost',
        )
        set_current_tenant(self.tenant)
        self.addCleanup(clear_current_tenant)
        self.client.defaults['HTTP_HOST'] = self.tenant.hostname

        self.admin = User.objects.create_superuser(
            username='photo-admin',
            email='photo-admin@example.test',
            password='test-password',
        )
        Profile.objects.update_or_create(user=self.admin, defaults={'is_approved': True})
        staff_group, _ = Group.objects.get_or_create(name='Staff')
        self.admin.groups.add(staff_group)
        self.client.force_login(self.admin)

    def make_photo_upload(self):
        image_bytes = BytesIO()
        Image.new('RGB', (120, 160), color='teal').save(image_bytes, format='PNG')
        return SimpleUploadedFile('passport.png', image_bytes.getvalue(), content_type='image/png')

    def test_school_admin_can_open_full_student_profile_from_class_roster(self):
        admin = User.objects.create_user(
            username='school-admin',
            email='school-admin@example.test',
            password='test-password',
        )
        Profile.objects.update_or_create(user=admin, defaults={'is_approved': True})
        TenantMembership.objects.create(user=admin, tenant=self.tenant, role='school_admin')

        school_class = SchoolClasses.objects.create(
            tenant=self.tenant,
            class_name='Primary 1',
        )
        student = Student.objects.create(
            tenant=self.tenant,
            admission_no='ROSTER001',
            surname='Roster',
            other_names='Student',
            student_class=school_class,
            student_phone='08012345678',
            student_email='roster@example.test',
            student_address='12 Class Road',
            guardian_name='Guardian Example',
            guardian_phone='08087654321',
        )
        self.client.force_login(admin)

        roster_response = self.client.get(
            reverse('school_classes:class_detail', args=[school_class.pk])
        )
        self.assertEqual(roster_response.status_code, 200)
        profile_url = reverse('students:student_detail', args=[student.pk])
        self.assertContains(roster_response, 'View Full Profile')
        self.assertContains(roster_response, f'href="{profile_url}"')

        profile_response = self.client.get(profile_url)
        self.assertEqual(profile_response.status_code, 200)
        self.assertContains(profile_response, '08012345678')
        self.assertContains(profile_response, 'roster@example.test')
        self.assertContains(profile_response, '12 Class Road')
        self.assertContains(profile_response, 'Guardian Example')
        self.assertContains(profile_response, '08087654321')

    def test_create_form_uploads_and_displays_student_photo(self):
        form_response = self.client.get(reverse('students:student_add'))
        self.assertEqual(form_response.status_code, 200)
        self.assertContains(form_response, 'enctype="multipart/form-data"')
        self.assertContains(form_response, 'name="photo"')

        response = self.client.post(
            reverse('students:student_add'),
            {
                'admission_no': 'PHOTO001',
                'surname': 'Portrait',
                'other_names': 'Learner',
                'student_phone': '08012345678',
                'student_email': 'learner@example.test',
                'student_address': '12 School Road',
                'guardian_name': 'Parent Example',
                'guardian_phone': '08087654321',
                'gender': 'F',
                'photo': self.make_photo_upload(),
            },
        )

        self.assertEqual(response.status_code, 302)
        student = Student._base_manager.get(admission_no='PHOTO001')
        self.assertTrue(student.photo.name.startswith('students/passports/'))
        self.assertTrue(student.photo.storage.exists(student.photo.name))

        detail_response = self.client.get(reverse('students:student_detail', args=[student.pk]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, student.photo.url)
        self.assertContains(detail_response, '08012345678')
        self.assertContains(detail_response, 'learner@example.test')
        self.assertContains(detail_response, 'Parent Example')
        self.assertContains(detail_response, '08087654321')

        admin_response = self.client.get(
            reverse('admin:students_student_change', args=[student.pk])
        )
        self.assertEqual(admin_response.status_code, 200)
        self.assertContains(admin_response, '08012345678')
        self.assertContains(admin_response, '12 School Road')
        self.assertContains(admin_response, 'Parent Example')

        student_user = User.objects.create_user(username='photo-student', password='test-password')
        student.user = student_user
        student.save(update_fields=['user'])
        self.client.force_login(student_user)
        profile_response = self.client.get(reverse('students:student_portal_profile'))
        self.assertEqual(profile_response.status_code, 200)
        self.assertContains(profile_response, student.photo.url)
        self.assertContains(profile_response, '08012345678')
        self.assertContains(profile_response, 'learner@example.test')
        self.assertContains(profile_response, '12 School Road')
        self.assertContains(profile_response, 'Parent Example')
        self.assertContains(profile_response, '08087654321')

    def test_admission_application_uploads_photo_and_transfers_it_when_accepted(self):
        response = self.client.get(reverse('students:student_application'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, 'name="photo"')

        response = self.client.post(
            reverse('students:student_application'),
            {
                'admission_number_requested': 'APPLY001',
                'first_name': 'Applicant',
                'last_name': 'Portrait',
                'student_address': '34 Application Lane',
                'student_phone': '08011223344',
                'student_email': 'applicant@example.test',
                'guardian_name': 'Parent',
                'photo': self.make_photo_upload(),
            },
        )

        self.assertEqual(response.status_code, 302)
        application = StudentApplication.objects.get(admission_number_requested='APPLY001')
        self.assertTrue(application.photo.name.startswith('students/passports/'))
        self.assertTrue(application.photo.storage.exists(application.photo.name))
        review_response = self.client.get(
            reverse('students:student_application_detail', args=[application.pk])
        )
        self.assertEqual(review_response.status_code, 200)
        self.assertContains(review_response, application.photo.url)

        application.status = 'accepted'
        application.save()
        student = Student._base_manager.get(admission_no='APPLY001')
        self.assertEqual(student.photo.name, application.photo.name)
        self.assertEqual(student.student_address, '34 Application Lane')
        self.assertEqual(student.student_phone, '08011223344')
        self.assertEqual(student.student_email, 'applicant@example.test')
        self.assertTrue(student.photo.storage.exists(student.photo.name))

    def test_student_can_view_but_cannot_upload_photo_from_own_profile(self):
        student_user = User.objects.create_user(username='self-photo-student', password='test-password')
        student = Student.objects.create(
            admission_no='SELF001',
            surname='Self',
            other_names='Upload',
            user=student_user,
            photo=self.make_photo_upload(),
        )
        original_photo_name = student.photo.name
        self.client.force_login(student_user)

        response = self.client.get(reverse('students:student_portal_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, student.photo.url)
        self.assertNotContains(response, 'name="photo"')
        self.assertNotContains(response, 'enctype="multipart/form-data"')

        response = self.client.post(
            reverse('students:student_portal_profile'),
            {'photo': self.make_photo_upload()},
        )

        self.assertEqual(response.status_code, 405)
        student.refresh_from_db()
        self.assertEqual(student.photo.name, original_photo_name)

    def test_non_admin_staff_cannot_upload_or_change_student_photo(self):
        student = Student.objects.create(
            admission_no='STAFF001',
            surname='Staff',
            other_names='Restricted',
            photo=self.make_photo_upload(),
        )
        original_photo_name = student.photo.name
        teacher = User.objects.create_user(username='photo-teacher', password='test-password')
        Profile.objects.update_or_create(user=teacher, defaults={'is_approved': True})
        teacher_group, _ = Group.objects.get_or_create(name='Teacher')
        teacher.groups.add(teacher_group)
        TenantMembership.objects.create(user=teacher, tenant=self.tenant, role='teacher')
        self.client.force_login(teacher)

        form_response = self.client.get(reverse('students:student_edit', args=[student.pk]))
        self.assertEqual(form_response.status_code, 200)
        self.assertNotContains(form_response, 'name="photo"')

        response = self.client.post(
            reverse('students:student_edit', args=[student.pk]),
            {
                'admission_no': student.admission_no,
                'surname': student.surname,
                'other_names': student.other_names,
                'photo': self.make_photo_upload(),
            },
        )

        self.assertEqual(response.status_code, 302)
        student.refresh_from_db()
        self.assertEqual(student.photo.name, original_photo_name)
