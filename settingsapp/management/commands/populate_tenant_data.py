from payroll.models import Staff, SalaryComponent, Payslip, PayrollDashboard, SchoolExpense, SchoolFee, StudentInvoice, StudentPayment
from psychomotor.models import StudentTraitRating, Trait, TraitCategory
from staff_attendance.models import StaffAttendance, StudentAttendanceSettings, AttendanceSettings
from django.core.management.base import BaseCommand

from settingsapp.models import Tenant, SchoolSettings
from school_classes.models import SchoolClasses
from students.models import Student
from announcements.models import Announcement
from exams.models import Term, Subject
from attendance.models import AttendanceRecord, AttendanceSession
from results.models import GradeScale


class Command(BaseCommand):
    help = 'Populate existing school data records with the default Daarul Bayaan tenant.'

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(slug='daarulbayaan').first()
        if not tenant:
            self.stdout.write(self.style.ERROR("Default Daarul Bayaan tenant not found. Run 'create_default_tenant' first."))
            return

        # Bind all existing records to the default tenant
        models_to_populate = [
            (SchoolClasses, 'classes'),
            (Student, 'students'),
            (Announcement, 'announcements'),
            (Term, 'terms'),
            (Subject, 'subjects'),
            (AttendanceRecord, 'attendance_records'),
            (AttendanceSession, 'attendance_sessions'),
            (GradeScale, 'grade_scales'),
            # Payroll models
            (Staff, 'staff'),
            (SalaryComponent, 'salary_components'),
            (Payslip, 'payslips'),
            (PayrollDashboard, 'payroll_dashboards'),
            (SchoolExpense, 'school_expenses'),
            (SchoolFee, 'school_fees'),
            (StudentInvoice, 'student_invoices'),
            (StudentPayment, 'student_payments'),
            # Psychomotor models
            (TraitCategory, 'trait_categories'),
            (Trait, 'traits'),
            (StudentTraitRating, 'student_trait_ratings'),
            # Staff Attendance models
            (StudentAttendanceSettings, 'student_attendance_settings'),
            (AttendanceSettings, 'attendance_settings'),
            (StaffAttendance, 'staff_attendance'),
        ]

        for model, name in models_to_populate:
            updated_count = model.objects.filter(tenant__isnull=True).update(tenant=tenant)
            if updated_count:
                self.stdout.write(self.style.SUCCESS(f"Updated {updated_count} {name} records"))
            else:
                self.stdout.write(self.style.WARNING(f"No {name} records to update"))

        self.stdout.write(self.style.SUCCESS("All school data is now bound to the Daarul Bayaan tenant!"))
