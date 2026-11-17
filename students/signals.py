import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StudentApplication, Student

logger = logging.getLogger(__name__)


@receiver(post_save, sender=StudentApplication)
def create_student_on_approval(sender, instance, created, **kwargs):
    """Auto-create Student record when application is approved"""
    if not created and instance.status == 'accepted':
        # Check if student already exists
        if not Student.objects.filter(admission_no=instance.admission_number_requested).exists():
            # Create the student record with guardian information
            student = Student.objects.create(
                admission_no=instance.admission_number_requested,
                surname=instance.last_name,
                other_names=f"{instance.first_name} {instance.other_names}".strip(),
                dob=instance.dob,
                student_address=instance.student_address,
                student_phone=instance.student_phone,
                student_email=instance.student_email,
                gender=instance.gender,
                photo=instance.photo,
                student_class=instance.desired_class,
                status='active',
                # Guardian information
                guardian_name=instance.guardian_name,
                guardian_relationship=instance.guardian_relationship,
                guardian_phone=instance.guardian_phone,
                guardian_email=instance.guardian_email,
                guardian_address=instance.guardian_address,
                guardian_occupation=instance.guardian_occupation,
                guardian_employer=instance.guardian_employer,
                emergency_contact_name=instance.emergency_contact_name,
                emergency_contact_phone=instance.emergency_contact_phone
            )
            logger.info("Created student record: %s", student)
        else:
            logger.warning(
                "Student with admission number %s already exists",
                instance.admission_number_requested,
            )