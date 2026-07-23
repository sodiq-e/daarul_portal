from django.test import RequestFactory, SimpleTestCase, TestCase

from .forms import SchoolSettingsForm
from .models import SchoolSettings
from .print_utils import build_document_verification, generate_document_reference


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
