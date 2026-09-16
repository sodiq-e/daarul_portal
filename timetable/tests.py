from datetime import time

from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db import IntegrityError
from django.test import RequestFactory, TestCase

from exams.models import ClassSubject, Subject, Term
from school_classes.models import ClassTeacher, SchoolClasses, Teacher
from settingsapp.models import Tenant
from settingsapp.tenant_utils import clear_current_tenant, set_current_tenant

from .models import TimetableDay, TimetableEntry, TimetableSlot, TimetableTemplate
from .views import timetable_edit_slot, timetable_fill


class TimetableModelTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='Timetable School',
            slug='timetable-school',
            hostname='timetable-school.example.com',
        )
        set_current_tenant(self.tenant)
        self.term = Term.objects.create(
            name='first', display_name='First Term', academic_year='2026/2027'
        )
        self.school_class = SchoolClasses.objects.create(class_name='Basic 1')
        self.subject = Subject.objects.create(name='Mathematics', code='MTH')
        self.class_subject = ClassSubject.objects.create(
            school_class=self.school_class, subject=self.subject
        )
        self.timetable = TimetableTemplate.objects.create(
            name='Basic 1 Weekly Timetable', term=self.term,
            school_class=self.school_class,
        )
        self.day = TimetableDay.objects.create(
            timetable=self.timetable, day='monday', order=0
        )
        self.slot = TimetableSlot.objects.create(
            timetable=self.timetable, label='Period 1',
            start_time=time(8), end_time=time(8, 40), order=0
        )

    def tearDown(self):
        clear_current_tenant()

    def test_entry_can_reference_only_the_class_subject_for_the_class(self):
        entry = TimetableEntry.objects.create(
            timetable=self.timetable,
            day=self.day,
            slot=self.slot,
            class_subject=self.class_subject,
        )
        self.assertEqual(entry.class_subject.school_class, self.school_class)
        self.assertEqual(TimetableEntry.objects.count(), 1)

    def test_grid_cells_are_unique(self):
        TimetableEntry.objects.create(
            timetable=self.timetable,
            day=self.day,
            slot=self.slot,
            class_subject=self.class_subject,
        )
        with self.assertRaises(IntegrityError):
            TimetableEntry.objects.create(
                timetable=self.timetable,
                day=self.day,
                slot=self.slot,
                class_subject=self.class_subject,
            )

    def test_teacher_can_fill_subject_by_name(self):
        user = get_user_model().objects.create_user(username='teacher-1', password='secret123')
        teacher = Teacher.objects.create(user=user, employee_id='T-1001', is_approved=True)
        ClassTeacher.objects.create(
            teacher=teacher,
            school_class=self.school_class,
            subject=self.subject,
            is_class_teacher=True,
            is_active=True,
        )

        factory = RequestFactory()
        request = factory.post(
            f'/timetable/{self.timetable.pk}/fill/',
            {f'entry_{self.day.id}_{self.slot.id}': 'Mathematics', f'note_{self.day.id}_{self.slot.id}': 'Room 5'},
        )
        request.user = user
        request.session = self.client.session
        setattr(request, '_messages', FallbackStorage(request))

        response = timetable_fill(request, self.timetable.pk)

        self.assertEqual(response.status_code, 302)
        entry = TimetableEntry.objects.get(timetable=self.timetable, day=self.day, slot=self.slot)
        self.assertEqual(entry.class_subject, self.class_subject)
        self.assertEqual(entry.teacher, teacher)
        self.assertEqual(entry.note, 'Room 5')

    def test_admin_can_edit_and_reorder_period(self):
        second_slot = TimetableSlot.objects.create(
            timetable=self.timetable, label='Period 2',
            start_time=time(8, 40), end_time=time(9, 20), order=1
        )
        user = get_user_model().objects.create_superuser(
            username='timetable-admin', password='secret123', email='admin@example.com'
        )

        factory = RequestFactory()
        request = factory.post(
            f'/timetable/{self.timetable.pk}/slots/{self.slot.pk}/edit/',
            {
                'label': 'Morning Period',
                'slot_type': 'period',
                'start_time': '09:00',
                'end_time': '09:45',
                'order': '1',
            },
        )
        request.user = user
        request.session = self.client.session
        setattr(request, '_messages', FallbackStorage(request))
        response = timetable_edit_slot(request, self.timetable.pk, self.slot.pk)

        self.assertEqual(response.status_code, 302)
        self.slot.refresh_from_db()
        second_slot.refresh_from_db()
        self.assertEqual(self.slot.label, 'Morning Period')
        self.assertEqual(str(self.slot.start_time), '09:00:00')
        self.assertEqual(self.slot.order, 1)
        self.assertEqual(second_slot.order, 0)
