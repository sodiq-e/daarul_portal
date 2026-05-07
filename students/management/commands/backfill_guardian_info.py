from django.core.management.base import BaseCommand
from students.models import Student, StudentApplication


class Command(BaseCommand):
    help = 'Backfill guardian information from StudentApplication to Student records'

    def handle(self, *args, **options):
        accepted_applications = StudentApplication.objects.filter(status='accepted')
        updated_count = 0

        for application in accepted_applications:
            try:
                student = Student.objects.get(admission_no=application.admission_number_requested)

                if not student.guardian_name and application.guardian_name:
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
                        self.style.SUCCESS(f'Updated guardian info for student: {student.full_name()}')
                    )
                else:
                    self.stdout.write(
                        f'Skipped {student.full_name()} - already has guardian info or application has none'
                    )

            except Student.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'No student found for application: {application.admission_number_requested}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing application {application.id}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} student records with guardian information')
        )