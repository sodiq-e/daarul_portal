from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db.models import Avg
from django.test import RequestFactory, TestCase

from exams.models import Subject, Term
from school_classes.models import ClassTeacher, SchoolClasses, Teacher
from settingsapp.models import Tenant
from settingsapp.tenant_utils import clear_current_tenant, set_current_tenant
from students.models import Student

from .models import Promotion, WeeklyAssessmentRecord
from .views import build_weekly_assessment_chart_data, promotions_list


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


class WeeklyAssessmentModelTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='Weekly Assessment School',
            slug='weekly-assessment-school',
            hostname='weekly-assessment.example.com',
        )
        set_current_tenant(self.tenant)
        self.school_class = SchoolClasses.objects.create(class_name='Basic 3')
        self.term = Term.objects.create(
            name='first',
            display_name='First Term',
            academic_year='2026/2027',
            is_active=True,
        )
        self.subject = Subject.objects.create(
            name='Mathematics',
            code='MATH',
            tenant=self.tenant,
        )
        from exams.models import ClassSubject
        self.class_subject = ClassSubject.objects.create(
            school_class=self.school_class,
            subject=self.subject,
            tenant=self.tenant,
        )
        self.student = Student.objects.create(
            admission_no='WEEK001',
            surname='Doe',
            other_names='Jane',
            student_class=self.school_class,
            status='active',
        )

    def tearDown(self):
        clear_current_tenant()

    def test_weekly_assessment_percentage_and_aggregate_are_calculated(self):
        assessment = WeeklyAssessmentRecord.objects.create(
            student=self.student,
            class_subject=self.class_subject,
            term=self.term,
            academic_year='2026/2027',
            week_number=1,
            assessment_date='2026-09-05',
            score=18,
            out_of=20,
        )

        self.assertEqual(assessment.percentage, 90.00)
        self.assertEqual(assessment.total_score, 18)
        self.assertEqual(assessment.average_score, 18.00)

        second_assessment = WeeklyAssessmentRecord.objects.create(
            student=self.student,
            class_subject=self.class_subject,
            term=self.term,
            academic_year='2026/2027',
            week_number=2,
            assessment_date='2026-09-12',
            score=16,
            out_of=20,
        )

        queryset = WeeklyAssessmentRecord.objects.filter(student=self.student, term=self.term)
        average = queryset.aggregate(avg_score=Avg('score'))['avg_score']
        self.assertEqual(float(average), 17.0)
        self.assertEqual(second_assessment.percentage, 80.00)


class WeeklyAssessmentBulkEntryTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='Bulk Weekly Assessment School',
            slug='bulk-weekly-assessment-school',
            hostname='bulk-weekly-assessment.example.com',
        )
        set_current_tenant(self.tenant)
        self.school_class = SchoolClasses.objects.create(class_name='Basic 4')
        self.term = Term.objects.create(
            name='first',
            display_name='First Term',
            academic_year='2026/2027',
            is_active=True,
        )
        self.subject = Subject.objects.create(
            name='English',
            code='ENG',
            tenant=self.tenant,
        )
        from exams.models import ClassSubject
        self.class_subject = ClassSubject.objects.create(
            school_class=self.school_class,
            subject=self.subject,
            tenant=self.tenant,
        )
        self.student = Student.objects.create(
            admission_no='WEEK002',
            surname='Smith',
            other_names='Alice',
            student_class=self.school_class,
            status='active',
        )
        self.user = get_user_model().objects.create_user(
            username='bulk-teacher',
            email='teacher@example.com',
            password='secret123',
        )
        self.teacher = Teacher.objects.create(
            user=self.user,
            employee_id='T-100',
            is_approved=True,
            tenant=self.tenant,
        )
        ClassTeacher.objects.create(
            tenant=self.tenant,
            teacher=self.teacher,
            school_class=self.school_class,
            subject=self.subject,
            is_active=True,
        )
        self.factory = RequestFactory()

    def test_bulk_weekly_assessment_entry_saves_scores(self):
        request = self.factory.post(
            f'/results/weekly-assessment/bulk-entry/{self.school_class.pk}/{self.term.pk}/',
            {
                'week_number': '3',
                'assessment_date': '2026-09-15',
                f'score_{self.student.pk}_{self.class_subject.pk}': '18',
                f'out_of_{self.student.pk}_{self.class_subject.pk}': '20',
                f'assessment_type_{self.student.pk}_{self.class_subject.pk}': 'quiz',
                f'remarks_{self.student.pk}_{self.class_subject.pk}': 'Very good progress',
            }
        )
        request.user = self.user
        request.session = self.client.session
        setattr(request, '_messages', FallbackStorage(request))

        from .views import bulk_weekly_assessment_entry
        response = bulk_weekly_assessment_entry(request, self.school_class.pk, self.term.pk)

        self.assertEqual(response.status_code, 302)
        record = WeeklyAssessmentRecord.objects.get(
            student=self.student,
            class_subject=self.class_subject,
            term=self.term,
            week_number=3,
        )
        self.assertEqual(float(record.score), 18)
        self.assertEqual(float(record.out_of), 20)
        self.assertEqual(record.assessment_type, 'quiz')
        self.assertEqual(record.remarks, 'Very good progress')

    def test_bulk_weekly_assessment_entry_updates_out_of_without_score(self):
        record = WeeklyAssessmentRecord.objects.create(
            student=self.student,
            class_subject=self.class_subject,
            term=self.term,
            academic_year=self.term.academic_year,
            week_number=3,
            assessment_date='2026-09-15',
            assessment_type='classwork',
            score=12,
            out_of=15,
            remarks='Old comment',
            created_by=self.user,
        )

        request = self.factory.post(
            f'/results/weekly-assessment/bulk-entry/{self.school_class.pk}/{self.term.pk}/',
            {
                'week_number': '3',
                'assessment_date': '2026-09-15',
                f'score_{self.student.pk}_{self.class_subject.pk}': '12',
                f'out_of_{self.student.pk}_{self.class_subject.pk}': '25',
                f'assessment_type_{self.student.pk}_{self.class_subject.pk}': 'quiz',
                f'remarks_{self.student.pk}_{self.class_subject.pk}': 'Updated remark',
            }
        )
        request.user = self.user
        request.session = self.client.session
        setattr(request, '_messages', FallbackStorage(request))

        from .views import bulk_weekly_assessment_entry
        response = bulk_weekly_assessment_entry(request, self.school_class.pk, self.term.pk)

        self.assertEqual(response.status_code, 302)
        record.refresh_from_db()
        self.assertEqual(float(record.out_of), 25)
        self.assertEqual(record.assessment_type, 'quiz')
        self.assertEqual(record.remarks, 'Updated remark')


class WeeklyAssessmentChartFilterTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='Chart Weekly Assessment School',
            slug='chart-weekly-assessment-school',
            hostname='chart-weekly-assessment.example.com',
        )
        set_current_tenant(self.tenant)
        self.school_class = SchoolClasses.objects.create(class_name='Basic 5')
        self.term = Term.objects.create(
            name='first',
            display_name='First Term',
            academic_year='2026/2027',
            is_active=True,
        )
        self.subject_math = Subject.objects.create(
            name='Mathematics',
            code='MATH',
            tenant=self.tenant,
        )
        self.subject_english = Subject.objects.create(
            name='English',
            code='ENG',
            tenant=self.tenant,
        )
        from exams.models import ClassSubject
        self.math_class_subject = ClassSubject.objects.create(
            school_class=self.school_class,
            subject=self.subject_math,
            tenant=self.tenant,
        )
        self.english_class_subject = ClassSubject.objects.create(
            school_class=self.school_class,
            subject=self.subject_english,
            tenant=self.tenant,
        )
        self.student = Student.objects.create(
            admission_no='WEEK003',
            surname='Brown',
            other_names='Chris',
            student_class=self.school_class,
            status='active',
        )
        WeeklyAssessmentRecord.objects.create(
            student=self.student,
            class_subject=self.math_class_subject,
            term=self.term,
            academic_year='2026/2027',
            week_number=1,
            assessment_date='2026-09-05',
            score=80,
            out_of=100,
        )
        WeeklyAssessmentRecord.objects.create(
            student=self.student,
            class_subject=self.math_class_subject,
            term=self.term,
            academic_year='2026/2027',
            week_number=2,
            assessment_date='2026-09-12',
            score=70,
            out_of=100,
        )
        WeeklyAssessmentRecord.objects.create(
            student=self.student,
            class_subject=self.english_class_subject,
            term=self.term,
            academic_year='2026/2027',
            week_number=1,
            assessment_date='2026-09-05',
            score=90,
            out_of=100,
        )

    def tearDown(self):
        clear_current_tenant()

    def test_chart_uses_week_labels_when_subject_filter_is_applied(self):
        queryset = WeeklyAssessmentRecord.objects.filter(student=self.student)
        labels, data = build_weekly_assessment_chart_data(
            queryset,
            academic_year='2026/2027',
            term_id=str(self.term.id),
            subject_id=str(self.subject_math.id),
            week_from='',
            week_to='',
        )

        self.assertEqual(labels, ['Week 1', 'Week 2'])
        self.assertEqual(data, [80.0, 70.0])

    def test_chart_uses_subject_labels_when_no_subject_filter_is_active(self):
        queryset = WeeklyAssessmentRecord.objects.filter(student=self.student)
        labels, data = build_weekly_assessment_chart_data(
            queryset,
            academic_year='2026/2027',
            term_id=str(self.term.id),
            subject_id='',
            week_from='',
            week_to='',
        )

        self.assertEqual(labels, ['English', 'Mathematics'])
        self.assertEqual(data, [90.0, 75.0])

    def tearDown(self):
        clear_current_tenant()
