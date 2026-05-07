#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daarul_portal.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from students.models import Student, StudentApplication

def backfill_guardian_info():
    """Backfill guardian information from StudentApplication to Student records"""
    accepted_applications = StudentApplication.objects.filter(status='accepted')
    updated_count = 0

    print(f"Found {accepted_applications.count()} accepted applications")

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
                print(f'✓ Updated guardian info for student: {student.full_name()}')
            else:
                print(f'Skipped {student.full_name()} - already has guardian info or application has none')

        except Student.DoesNotExist:
            print(f'⚠ No student found for application: {application.admission_number_requested}')
        except Exception as e:
            print(f'✗ Error processing application {application.id}: {str(e)}')

    print(f'Successfully updated {updated_count} student records with guardian information')

if __name__ == '__main__':
    backfill_guardian_info()