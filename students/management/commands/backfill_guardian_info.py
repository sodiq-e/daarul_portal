from django.core.management.base import BaseCommand
from students.models import Student, StudentApplication


class Command(BaseCommand):
    help = 'Backfill guardian information from StudentApplication to Student records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if student already has guardian info',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        accepted_applications = StudentApplication.objects.filter(status='accepted')
        updated_count = 0
        skipped_count = 0

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('POPULATING GUARDIAN INFORMATION FOR STUDENTS'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'\nFound {accepted_applications.count()} accepted applications\n')

        for application in accepted_applications:
            try:
                student = Student.objects.get(admission_no=application.admission_number_requested)

                # Check if we should update
                should_update = force or not student.guardian_name

                if should_update and application.guardian_name:
                    student.guardian_name = application.guardian_name
                    student.guardian_relationship = application.guardian_relationship
                    student.guardian_phone = application.guardian_phone
                    student.guardian_email = application.guardian_email
                    student.guardian_address = application.guardian_address
                    student.guardian_occupation = application.guardian_occupation
                    student.guardian_employer = application.guardian_employer
                    student.emergency_contact_name = application.emergency_contact_name
                    student.emergency_contact_phone = application.emergency_contact_phone
                    student.save()

                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ UPDATED: {student.full_name()} - Guardian: {application.guardian_name}')
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        f'⊘ SKIPPED: {student.full_name()} - already has guardian info'
                    )

            except Student.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'✗ NOT FOUND: No student for admission #{application.admission_number_requested}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ ERROR with {application.admission_number_requested}: {str(e)}')
                )

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS(f'SUMMARY:'))
        self.stdout.write(self.style.SUCCESS(f'  ✓ Updated: {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'  ⊘ Skipped: {skipped_count}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('\nDone! Guardian information is now available in student profiles.'))
        self.stdout.write(self.style.SUCCESS('Teachers viewing student details will see parent contact information.\n'))