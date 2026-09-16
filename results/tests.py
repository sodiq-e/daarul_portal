from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase

from exams.models import Term
from school_classes.models import SchoolClasses
from settingsapp.models import Tenant
from settingsapp.tenant_utils import clear_current_tenant, set_current_tenant
from students.models import Student

from .models import Promotion
from .views import promotions_list


class PromotionWorkflowTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='Promotion School',
            slug='promotion-school',
            hostname='promotion-school.example.com',
        )
        set_current_tenant(self.tenant)
        self.user = get_user_model().objects.create_superuser(
            username='promotion-admin',
            password='secret123',
            email='admin@example.com',
        )
        self.source_class = SchoolClasses.objects.create(class_name='Basic 1')
        self.target_class = SchoolClasses.objects.create(class_name='Basic 2')
        self.term = Term.objects.create(
            name='first',
            display_name='First Term',
            academic_year='2026/2027',
            is_active=True,
        )
        self.student = Student.objects.create(
            admission_no='PROMO001',
            surname='Test',
            other_names='Student',
            student_class=self.source_class,
            status='active',
        )
        self.factory = RequestFactory()

    def tearDown(self):
        clear_current_tenant()

    def test_bulk_promotion_updates_student_class(self):
        request = self.factory.post('/results/promotions/', {
            'source_class': str(self.source_class.pk),
            'target_class': str(self.target_class.pk),
            'term': str(self.term.pk),
            'student_ids': [str(self.student.pk)],
            'remarks': 'Promoted after successful term.',
        })
        request.user = self.user
        request.session = self.client.session
        setattr(request, '_messages', FallbackStorage(request))

        response = promotions_list(request)

        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertEqual(self.student.student_class_id, self.target_class.id)
        self.assertTrue(Promotion.objects.filter(
            student=self.student,
            from_class=self.source_class,
            to_class=self.target_class,
            term=self.term,
        ).exists())

    def test_selected_student_without_target_class_moves_to_next_class(self):
        request = self.factory.post('/results/promotions/', {
            'source_class': '',
            'target_class': '',
            'term': str(self.term.pk),
            'student_ids': [str(self.student.pk)],
            'remarks': 'Automatic next-class promotion.',
        })
        request.user = self.user
        request.session = self.client.session
        setattr(request, '_messages', FallbackStorage(request))

        response = promotions_list(request)

        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertEqual(self.student.student_class_id, self.target_class.id)
        self.assertTrue(Promotion.objects.filter(
            student=self.student,
            from_class=self.source_class,
            to_class=self.target_class,
            term=self.term,
        ).exists())
