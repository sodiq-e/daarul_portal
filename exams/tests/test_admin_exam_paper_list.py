from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from exams.models import ExamPaper, Subject, Term
from exams.views import AdminExamPaperListView
from school_classes.models import SchoolClasses
from settingsapp.models import Tenant
from settingsapp.tenant_utils import clear_current_tenant, set_current_tenant


class AdminExamPaperListSearchTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='Exam Search School',
            slug='exam-search-school',
            hostname='exam-search-school.localhost',
        )
        set_current_tenant(self.tenant)
        self.addCleanup(clear_current_tenant)

        self.teacher = User.objects.create_user(
            username='exam-author',
            password='test-password',
            first_name='Exam',
            last_name='Author',
        )
        self.exam_paper = ExamPaper.objects.create(
            subject=Subject.objects.create(name='Mathematics', code='MATH'),
            school_class=SchoolClasses.objects.create(class_name='Primary 1'),
            term=Term.objects.create(
                name='first',
                display_name='First Term',
                academic_year='2026/2027',
            ),
            teacher=self.teacher,
            academic_session='2026/2027',
        )

    def test_search_matches_teacher_username(self):
        view = AdminExamPaperListView()
        view.request = RequestFactory().get(
            '/exams/admin/exam-papers/',
            {'q': self.teacher.username},
        )

        self.assertIn(self.exam_paper, view.get_queryset())

    def test_class_filter_returns_only_papers_for_selected_class(self):
        other_class = SchoolClasses.objects.create(class_name='Primary 2')
        other_paper = ExamPaper.objects.create(
            subject=self.exam_paper.subject,
            school_class=other_class,
            term=self.exam_paper.term,
            teacher=self.teacher,
            academic_session='2026/2027',
        )
        view = AdminExamPaperListView()
        view.request = RequestFactory().get(
            '/exams/admin/exam-papers/',
            {'school_class': str(self.exam_paper.school_class_id)},
        )

        self.assertEqual(list(view.get_queryset()), [self.exam_paper])
        self.assertNotIn(other_paper, view.get_queryset())

    def test_subject_filter_returns_only_papers_for_selected_subject(self):
        other_subject = Subject.objects.create(name='Science', code='SCI')
        other_paper = ExamPaper.objects.create(
            subject=other_subject,
            school_class=self.exam_paper.school_class,
            term=self.exam_paper.term,
            teacher=self.teacher,
            academic_session='2026/2027',
        )
        view = AdminExamPaperListView()
        view.request = RequestFactory().get(
            '/exams/admin/exam-papers/',
            {'subject': str(self.exam_paper.subject_id)},
        )

        self.assertEqual(list(view.get_queryset()), [self.exam_paper])
        self.assertNotIn(other_paper, view.get_queryset())
