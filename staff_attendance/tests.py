from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from school_classes.models import Teacher
from staff_attendance.models import StaffAttendance
from staff_attendance.views import AdminStaffAttendanceReportView, get_or_create_attendance_teacher_for_user


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
