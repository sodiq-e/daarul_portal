from django.contrib.auth.models import User
from django.test import TestCase

from exams.forms import ExamPaperForm
from exams.models import ClassSubject, Subject, Term
from school_classes.models import ClassTeacher, SchoolClasses, Teacher
from settingsapp.models import Tenant
from settingsapp.tenant_utils import clear_current_tenant, set_current_tenant


class ExamPaperFormSubjectTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='Exam Paper School',
            slug='exam-paper-school',
            hostname='exam-paper-school.localhost',
        )
        set_current_tenant(self.tenant)
        self.addCleanup(clear_current_tenant)

        self.user = User.objects.create_user(
            username='exam-teacher',
            password='test-password',
        )
        self.teacher = Teacher.objects.create(user=self.user, tenant=self.tenant)
        self.school_class = SchoolClasses.objects.create(
            tenant=self.tenant,
            class_name='Primary 1',
        )
        self.subject = Subject._base_manager.create(
            tenant=None,
            name='Shared Mathematics',
            code='MATH',
            is_active=True,
        )
        ClassSubject.objects.create(
            tenant=self.tenant,
            school_class=self.school_class,
            subject=self.subject,
        )
        ClassTeacher.objects.create(
            tenant=self.tenant,
            teacher=self.teacher,
            school_class=self.school_class,
            subject=self.subject,
            is_active=True,
        )
        self.term = Term.objects.create(
            tenant=self.tenant,
            name='first',
            display_name='First Term',
            academic_year='2026/2027',
            is_active=True,
        )

    def test_teacher_can_save_exam_paper_for_shared_subject_assigned_to_class(self):
        form = ExamPaperForm(
            data={
                'subject': str(self.subject.pk),
                'school_class': str(self.school_class.pk),
                'term': str(self.term.pk),
                'academic_session': '2026/2027',
                'duration': '1 Hour',
                'total_marks': '100',
                'instructions': '',
            },
            teacher=self.teacher,
        )

        self.assertTrue(form.is_valid(), form.errors)
        exam_paper = form.save(commit=False)
        self.assertEqual(exam_paper.subject, self.subject)
        self.assertEqual(exam_paper.school_class, self.school_class)

    def test_teacher_cannot_select_subject_not_assigned_to_selected_class(self):
        other_subject = Subject._base_manager.create(
            tenant=None,
            name='Unassigned Science',
            code='SCI',
            is_active=True,
        )
        form = ExamPaperForm(
            data={
                'subject': str(other_subject.pk),
                'school_class': str(self.school_class.pk),
                'term': str(self.term.pk),
                'academic_session': '2026/2027',
                'duration': '1 Hour',
                'total_marks': '100',
                'instructions': '',
            },
            teacher=self.teacher,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('subject', form.errors)
