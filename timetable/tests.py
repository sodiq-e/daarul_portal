from datetime import time

from django.db import IntegrityError
from django.test import TestCase

from exams.models import ClassSubject, Subject, Term
from school_classes.models import SchoolClasses
from settingsapp.models import Tenant
from settingsapp.tenant_utils import clear_current_tenant, set_current_tenant

from .models import TimetableDay, TimetableEntry, TimetableSlot, TimetableTemplate


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
