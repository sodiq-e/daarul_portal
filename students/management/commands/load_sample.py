from django.core.management.base import BaseCommand
from students.models import Student
from exams.models import Exam, Subject
from results.models import Score
import datetime
class Command(BaseCommand):
    help = 'Load sample data'
    def handle(self, *args, **options):
        s1 = Student.objects.create(admission_no='ADM001', surname='Ali', other_names='Ahmed')
        s2 = Student.objects.create(admission_no='ADM002', surname='Fatima', other_names='Bayo')
        sub1 = Subject.objects.create(name='Mathematics')
        sub2 = Subject.objects.create(name='English')
        exam = Exam.objects.create(name='First Term', date=datetime.date.today())
        Score.objects.create(student=s1, exam=exam, subject=sub1, score=85)
        Score.objects.create(student=s1, exam=exam, subject=sub2, score=78)
        Score.objects.create(student=s2, exam=exam, subject=sub1, score=72)
        Score.objects.create(student=s2, exam=exam, subject=sub2, score=66)
        self.stdout.write(self.style.SUCCESS('Sample data created'))
