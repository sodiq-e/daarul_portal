from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from school_classes.models import Teacher
from settingsapp.models import Tenant
from settingsapp.tenant_utils import clear_current_tenant, set_current_tenant
from staff_attendance.models import StaffAttendance, StudentAttendanceSettings
from staff_attendance.views import (
    AdminStaffAttendanceReportView,
    StudentAttendanceSettingsView,
    get_or_create_attendance_teacher_for_user,
)


class StaffAttendanceAdminAccessTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = get_user_model().objects.create_user(
            username='admin_clock_user',
            password='secret123',
            is_staff=True,
            is_superuser=True,
        )
        self.teacher_user = get_user_model().objects.create_user(
            username='teacher_clock_user',
            password='secret123',
        )

    def test_admin_user_gets_attendance_teacher_profile(self):
        teacher = get_or_create_attendance_teacher_for_user(self.admin_user)

        self.assertIsNotNone(teacher)
        self.assertEqual(teacher.user, self.admin_user)
        self.assertTrue(Teacher.objects.filter(user=self.admin_user).exists())

    def test_admin_report_filters_by_teacher_and_date_range(self):
        teacher_one = Teacher.objects.create(user=self.teacher_user, employee_id='T-101', is_approved=True)
        teacher_two = Teacher.objects.create(user=self.admin_user, employee_id='A-001', is_approved=True)

        today = timezone.localdate()
        target_start = today - timedelta(days=10)
        target_end = today - timedelta(days=7)

        StaffAttendance.objects.create(
            teacher=teacher_one,
            date=today - timedelta(days=7),
            clock_in=timezone.now() - timedelta(days=7, hours=2),
            clock_out=timezone.now() - timedelta(days=7, hours=1),
            clock_in_status=StaffAttendance.STATUS_PRESENT,
        )
        StaffAttendance.objects.create(
            teacher=teacher_one,
            date=today - timedelta(days=6),
            clock_in=timezone.now() - timedelta(days=6, hours=2),
            clock_out=timezone.now() - timedelta(days=6, hours=1),
            clock_in_status=StaffAttendance.STATUS_LATE,
        )
        StaffAttendance.objects.create(
            teacher=teacher_two,
            date=today - timedelta(days=3),
            clock_in=timezone.now() - timedelta(days=3, hours=2),
            clock_out=timezone.now() - timedelta(days=3, hours=1),
            clock_in_status=StaffAttendance.STATUS_PRESENT,
        )

        request = self.factory.get(
            '/staff-attendance/admin-report/',
            {'teacher': teacher_one.pk, 'start_date': target_start.isoformat(), 'end_date': target_end.isoformat()},
        )
        request.user = self.admin_user

        view = AdminStaffAttendanceReportView()
        view.request = request

        records = list(view.get_queryset())

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].teacher, teacher_one)


class StudentAttendanceSettingsTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='Student Attendance School',
            slug='student-attendance-school',
            hostname='student-attendance-school.example.com',
        )
        set_current_tenant(self.tenant)
        self.admin_user = get_user_model().objects.create_superuser(
            username='student-settings-admin',
            password='secret123',
            email='admin@example.com',
        )
        self.factory = RequestFactory()

    def tearDown(self):
        clear_current_tenant()

    def test_settings_save_keeps_one_active_tenant_row(self):
        existing = StudentAttendanceSettings.objects.create(
            tenant=self.tenant,
            absence_threshold_warning=5,
            active=True,
        )
        request = self.factory.post('/staff-attendance/student-settings/', {
            'enable_student_attendance': 'on',
            'require_daily_checkin': 'on',
            'allow_parent_reason_submission': 'on',
            'absence_threshold_warning': '10',
            'active': 'on',
        })
        request.user = self.admin_user
        request.tenant = self.tenant

        view = StudentAttendanceSettingsView()
        view.request = request
        form = view.get_form()

        self.assertTrue(form.is_valid())
        self.assertEqual(form.instance.pk, existing.pk)
        saved = form.save()

        self.assertEqual(saved.pk, existing.pk)
        self.assertEqual(StudentAttendanceSettings.objects.filter(active=True).count(), 1)
        self.assertEqual(saved.absence_threshold_warning, 10)
        self.assertEqual(saved.tenant_id, self.tenant.id)
