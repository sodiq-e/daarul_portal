#!/usr/bin/env python
"""
Quick script to update existing student records with guardian info from applications.
Run this in Django shell: python manage.py shell < populate_guardian_info.py
"""

from students.models import Student, StudentApplication

print("=" * 60)
print("POPULATING GUARDIAN INFORMATION FOR EXISTING STUDENTS")
print("=" * 60)

# Get all accepted applications
accepted_apps = StudentApplication.objects.filter(status='accepted')
print(f"\nFound {accepted_apps.count()} accepted applications")

updated = 0
skipped = 0
errors = 0

for app in accepted_apps:
    try:
        # Find student by admission number
        student = Student.objects.get(admission_no=app.admission_number_requested)
        
        # Only update if student doesn't already have guardian info
        if student.guardian_name:
            print(f"⊘ SKIP: {student.full_name()} already has guardian info")
            skipped += 1
            continue
        
        # Update all guardian fields
        student.guardian_name = app.guardian_name
        student.guardian_relationship = app.guardian_relationship
        student.guardian_phone = app.guardian_phone
        student.guardian_email = app.guardian_email
        student.guardian_address = app.guardian_address
        student.guardian_occupation = app.guardian_occupation
        student.guardian_employer = app.guardian_employer
        student.emergency_contact_name = app.emergency_contact_name
        student.emergency_contact_phone = app.emergency_contact_phone
        student.save()
        
        print(f"✓ UPDATED: {student.full_name()} - Guardian: {app.guardian_name}")
        updated += 1
        
    except Student.DoesNotExist:
        print(f"✗ NOT FOUND: No student record for admission #{app.admission_number_requested}")
        errors += 1
    except Exception as e:
        print(f"✗ ERROR with {app.admission_number_requested}: {str(e)}")
        errors += 1

print("\n" + "=" * 60)
print(f"SUMMARY:")
print(f"  ✓ Updated: {updated}")
print(f"  ⊘ Skipped: {skipped}")
print(f"  ✗ Errors:  {errors}")
print("=" * 60)
print("\nDone! Guardian information is now available in student profiles.")
print("Teachers viewing student details will see parent contact information.")
