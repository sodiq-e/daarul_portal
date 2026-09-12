from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from .forms import SchoolSettingsForm
from .models import GalleryImage, SchoolSettings, Tenant, TenantMembership
from .print_utils import build_document_verification, generate_document_reference
from .tenant_utils import clear_current_tenant, resolve_tenant, set_current_tenant, user_has_tenant_access
from .middleware import TenantMiddleware

from announcements.models import Announcement
from school_classes.models import Teacher
from staff_attendance.models import AttendanceSettings
from accounts.models import Profile


class SchoolSettingsFormTests(TestCase):
    def test_form_accepts_default_hero_settings_without_extra_post_data(self):
        instance = SchoolSettings.objects.create()
        data = {
            'school_name': 'Test School',
            'motto': 'Knowledge for the Fear of God',
            'primary_color': '#4b2e83',
            'secondary_color': '#7f5af0',
            'accent_color': '#ffc107',
            'background_color': '#f5f5ff',
            'text_color': '#202040',
            'heading_text_color': '#2a2a2a',
            'icon_plate_color': '#e8e0ff',
            'header_heading_color': '#ffffff',
            'icon_color': '#4b2e83',
            'hero_title_font_size': 'clamp(2.5rem, 4.8vw, 4.3rem)',
            'hero_intro_font_size': 'clamp(0.95rem, 1.35vw, 1.05rem)',
            'hero_rotator_title_font_size': 'clamp(1.25rem, 2.2vw, 1.75rem)',
            'hero_rotator_subtitle_font_size': 'clamp(0.95rem, 1.4vw, 1.05rem)',
            'hero_title_color': '#ffffff',
            'hero_text_color': '#f5f7ff',
            'hero_button_font_size': '0.82rem',
            'hero_button_text_color': '#ffffff',
            'hero_button_background_color': '#4b2e83',
            'hero_button_border_color': '#ffffff',
            'hero_button_hover_background_color': '#ffffff',
            'hero_button_hover_text_color': '#4b2e83',
            'hero_content_animation_style': 'fade',
            'hero_eyebrow_font_size': 'clamp(0.8rem, 1.1vw, 0.95rem)',
            'hero_eyebrow_animation_style': 'slide-up',
        }

        form = SchoolSettingsForm(data=data, instance=instance)

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['hero_overlay_opacity'], 50)
        self.assertEqual(form.cleaned_data['hero_text_position'], 'left')
        self.assertEqual(form.cleaned_data['hero_animation_speed'], 900)
        self.assertEqual(form.cleaned_data['hero_content_animation_style'], 'fade')
        self.assertEqual(form.cleaned_data['hero_eyebrow_font_size'], 'clamp(0.8rem, 1.1vw, 0.95rem)')
        self.assertEqual(form.cleaned_data['hero_eyebrow_animation_style'], 'slide-up')

    def test_form_uses_existing_values_for_blank_color_fields(self):
        instance = SchoolSettings.objects.create(
            primary_color='#123456',
            secondary_color='#654321',
            accent_color='#abcdef',
            background_color='#fedcba',
            text_color='#112233',
            heading_text_color='#445566',
            icon_plate_color='#778899',
            header_heading_color='#aabbcc',
            icon_color='#ddeeff',
        )
        data = {
            'school_name': 'Test School',
            'motto': 'Knowledge for the Fear of God',
            'primary_color': '',
            'secondary_color': '',
            'accent_color': '',
            'background_color': '',
            'text_color': '',
            'heading_text_color': '',
            'icon_plate_color': '',
            'header_heading_color': '',
            'icon_color': '',
        }

        form = SchoolSettingsForm(data=data, instance=instance)

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['primary_color'], '#123456')
        self.assertEqual(form.cleaned_data['secondary_color'], '#654321')


class TenantScopeTests(TestCase):
    def test_tenant_can_be_created_with_unique_hostname(self):
        tenant = Tenant.objects.create(
            name='School A',
            slug='schoola',
            hostname='schoola.oyo.com',
            is_active=True,
        )

        self.assertEqual(str(tenant), 'School A')
        self.assertEqual(tenant.slug, 'schoola')
        self.assertEqual(tenant.hostname, 'schoola.oyo.com')

    def test_school_settings_can_be_linked_to_a_tenant(self):
        tenant = Tenant.objects.create(
            name='Daarul Bayaan',
            slug='daarulbayaan-test',
            hostname='daarulbayaan-test.localhost',
            is_active=True,
        )

        settings = SchoolSettings.objects.create(
            tenant=tenant,
            school_name='Daarul Bayaan Islamic School',
        )

        self.assertEqual(settings.tenant, tenant)
        self.assertEqual(settings.school_name, 'Daarul Bayaan Islamic School')

    def test_gallery_page_only_shows_active_tenant_media(self):
        tenant_a = Tenant.objects.create(
            name='School A',
            slug='school-a-gallery',
            hostname='school-a-gallery.localhost',
            is_active=True,
        )
        tenant_b = Tenant.objects.create(
            name='School B',
            slug='school-b-gallery',
            hostname='school-b-gallery.localhost',
            is_active=True,
        )
        settings_a = SchoolSettings.objects.create(tenant=tenant_a, school_name='School A')
        settings_b = SchoolSettings.objects.create(tenant=tenant_b, school_name='School B')
        GalleryImage.objects.create(school_settings=settings_a, title='A gallery image')
        GalleryImage.objects.create(school_settings=settings_b, title='B gallery image')

        response = self.client.get('/gallery/', HTTP_HOST=tenant_a.hostname)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A gallery image')
        self.assertNotContains(response, 'B gallery image')

    @override_settings(ALLOWED_HOSTS=['prep1.localhost'])
    def test_approved_teacher_gets_teacher_sidebar(self):
        from django.contrib.auth import get_user_model

        tenant = Tenant.objects.create(
            name='PREP1 School',
            slug='prep1',
            hostname='prep1.localhost',
            is_active=True,
        )
        user = get_user_model().objects.create_user(
            username='prep1-teacher',
            password='testpass123',
        )
        profile = Profile.objects.get(user=user)
        profile.requested_group = 'Teacher'
        profile.is_approved = True
        profile.save()
        Teacher.objects.create(
            user=user,
            tenant=tenant,
            employee_id='PREP1001',
            is_approved=True,
        )
        TenantMembership.objects.create(user=user, tenant=tenant, role='teacher', is_active=True)
        self.client.force_login(user)

        response = self.client.get('/', HTTP_HOST='prep1.localhost')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEACHER')
        self.assertNotContains(response, '>ADMIN<')


class TenantResolutionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = Tenant.objects.create(
            name='School A',
            slug='schoola',
            hostname='schoola.onlinehost.com',
            is_active=True,
        )

    def tearDown(self):
        self.tenant.delete()
        super().tearDown()

    @override_settings(TENANT_BASE_DOMAIN='localhost', ALLOWED_HOSTS=['localhost', '.localhost'])
    def test_localhost_platform_domain_and_subdomain_resolution(self):
        self.assertIsNone(resolve_tenant(self.factory.get('/', HTTP_HOST='localhost:8000')))
        self.assertEqual(
            resolve_tenant(self.factory.get('/', HTTP_HOST='schoola.localhost:8000')),
            self.tenant,
        )

    @override_settings(TENANT_BASE_DOMAIN='onlinehost.com', ALLOWED_HOSTS=['onlinehost.com', '.onlinehost.com'])
    def test_configured_online_platform_domain_and_subdomain_resolution(self):
        self.assertIsNone(resolve_tenant(self.factory.get('/', HTTP_HOST='onlinehost.com')))
        self.assertEqual(
            resolve_tenant(self.factory.get('/', HTTP_HOST='schoola.onlinehost.com')),
            self.tenant,
        )
        self.assertIsNone(resolve_tenant(self.factory.get('/', HTTP_HOST='unknown.onlinehost.com')))
        self.assertIsNone(resolve_tenant(self.factory.get('/', HTTP_HOST='www.onlinehost.com')))

    @override_settings(TENANT_BASE_DOMAIN='localhost')
    def test_tenant_form_normalizes_url_hostname(self):
        from .forms import TenantForm

        form = TenantForm(data={
            'name': 'School A',
            'slug': 'schoolb',
            'hostname': 'http://schoolb.localhost:8001/',
            'is_active': 'on',
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['hostname'], 'schoolb.localhost')


class DocumentVerificationUtilsTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_generate_document_reference_uses_prefix_and_format(self):
        reference = generate_document_reference("announcement")
        parts = reference.split("-")

        self.assertEqual(parts[0], "ANNOUNCEMENT")
        self.assertEqual(len(parts), 3)
        self.assertTrue(len(parts[1]) == 8)
        self.assertTrue(len(parts[2]) >= 4)

    def test_build_document_verification_includes_qr_and_url(self):
        request = self.factory.get('/announcements/1/')
        verification = build_document_verification(request, prefix="announcement")

        self.assertTrue(verification["enabled"])
        self.assertIn("reference", verification)
        self.assertIn("qr_svg", verification)
        self.assertIn("document_url", verification)
        self.assertIn("announcement", verification["reference"].lower())
        self.assertIn("<svg", verification["qr_svg"])


class TenantQueryProtectionTests(TestCase):
    def tearDown(self):
        clear_current_tenant()
        super().tearDown()

    def test_tenant_scoped_manager_filters_by_active_tenant_automatically(self):
        tenant_a = Tenant.objects.create(name='Alpha', slug='alpha', hostname='alpha.example.com', is_active=True)
        tenant_b = Tenant.objects.create(name='Beta', slug='beta', hostname='beta.example.com', is_active=True)

        user = self.user = __import__('django.contrib.auth').contrib.auth.models.User.objects.create_user(
            username='alpha-user',
            password='testpass123'
        )

        Announcement.objects.create(tenant=tenant_a, title='Alpha post', content='Alpha content', created_by=user, is_active=True)
        Announcement.objects.create(tenant=tenant_b, title='Beta post', content='Beta content', created_by=user, is_active=True)

        set_current_tenant(tenant_a)

        self.assertEqual(list(Announcement.objects.values_list('title', flat=True)), ['Alpha post'])
        self.assertEqual(Announcement.objects.count(), 1)
        self.assertEqual(Announcement.objects.get().tenant, tenant_a)

    def test_user_with_active_tenant_membership_has_access(self):
        tenant = Tenant.objects.create(name='School A', slug='school-a', hostname='schoola.example.com', is_active=True)
        user = __import__('django.contrib.auth').contrib.auth.models.User.objects.create_user(
            username='school-admin',
            password='testpass123'
        )

        TenantMembership.objects.create(user=user, tenant=tenant, role='school_admin', is_active=True)

        self.assertTrue(user_has_tenant_access(user, tenant))
        self.assertTrue(user_has_tenant_access(user, tenant, roles=['school_admin']))

        membership = user.tenant_memberships.get(tenant=tenant)
        membership.is_active = False
        membership.save()

        self.assertFalse(user_has_tenant_access(user, tenant))

    @override_settings(ALLOWED_HOSTS=['tenant-a.localhost', 'tenant-b.localhost', 'localhost'])
    def test_teacher_profile_is_not_visible_on_another_tenant(self):
        from django.contrib.auth import get_user_model

        tenant_a = Tenant.objects.create(name='Tenant A', slug='tenant-a', hostname='tenant-a.localhost', is_active=True)
        tenant_b = Tenant.objects.create(name='Tenant B', slug='tenant-b', hostname='tenant-b.localhost', is_active=True)
        user = get_user_model().objects.create_user(username='cross-tenant-teacher', password='testpass123')
        teacher = Teacher._base_manager.create(user=user, tenant=tenant_a, employee_id='CROSS001')

        request_factory = RequestFactory()

        def inspect_profile(request):
            profile = getattr(request.user, 'teacher_profile', None)
            return profile.tenant_id if profile else None

        with self.subTest(host='tenant-a.localhost'):
            request = request_factory.get('/', HTTP_HOST='tenant-a.localhost')
            request.user = user
            TenantMiddleware(inspect_profile)(request)
            self.assertEqual(inspect_profile(request), tenant_a.id)

        request = request_factory.get('/', HTTP_HOST='tenant-b.localhost')
        request.user = user
        TenantMiddleware(inspect_profile)(request)
        self.assertIsNone(inspect_profile(request))
        teacher.delete()

    def test_new_tenant_model_save_inherits_active_tenant(self):
        from students.models import Student

        tenant = Tenant.objects.create(name='Save School', slug='save-school', hostname='save-school.localhost')
        set_current_tenant(tenant)
        student = Student.objects.create(admission_no='SAVE001', surname='Saved', other_names='Student')
        self.assertEqual(student.tenant_id, tenant.id)

    def test_attendance_settings_are_isolated_per_tenant(self):
        tenant_a = Tenant.objects.create(name='Attendance A', slug='attendance-a', hostname='attendance-a.localhost')
        tenant_b = Tenant.objects.create(name='Attendance B', slug='attendance-b', hostname='attendance-b.localhost')
        set_current_tenant(tenant_a)
        AttendanceSettings.objects.create(active=True, allowed_radius_meters=100)
        set_current_tenant(tenant_b)
        AttendanceSettings.objects.create(active=True, allowed_radius_meters=200)

        self.assertEqual(AttendanceSettings.objects.current().allowed_radius_meters, 200)
        set_current_tenant(tenant_a)
        self.assertEqual(AttendanceSettings.objects.current().allowed_radius_meters, 100)
