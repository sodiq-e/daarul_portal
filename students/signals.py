from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StudentApplication, Student


@receiver(post_save, sender=StudentApplication)
def create_student_on_approval(sender, instance, created, **kwargs):
    """Auto-create Student record when application is approved"""
    if not created and instance.status == 'accepted':
        # Check if student already exists
        if not Student.objects.filter(admission_no=instance.admission_number_requested).exists():
            # Create the student record
            student = Student.objects.create(
                admission_no=instance.admission_number_requested,
                surname=instance.last_name,
                other_names=f"{instance.first_name} {instance.other_names}".strip(),
                dob=instance.dob,
                gender=instance.gender,
                student_class=instance.desired_class,
                status='active'
            )
            print(f"✓ Created student record: {student}")
        else:
            print(f"⚠ Student with admission number {instance.admission_number_requested} already exists")