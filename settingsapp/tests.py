from django.test import RequestFactory, SimpleTestCase

from .print_utils import build_document_verification, generate_document_reference


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
