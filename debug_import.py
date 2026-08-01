import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daarul_portal.settings')
import django
django.setup()
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from exams.models import Subject
from cbt.models import CBTExam
from cbt.views import import_exam_questions

User = get_user_model()
user = User.objects.create(username='debug_teacher', is_staff=True)
user.set_password('pass')
user.save()
subject, _ = Subject.objects.get_or_create(name='Mathematics', defaults={'code': 'MATH'})
exam = CBTExam.objects.create(name='DebugExam', created_by=user, allow_ai_questions=False, subject=subject)

request = RequestFactory().post(reverse('teacher_cbt:import_questions', kwargs={'exam_pk': exam.pk}), {
    'file': SimpleUploadedFile(
        'questions.json',
        b'[{"prompt":"What is 3+3?","question_type":"mcq","mark_value":1,"difficulty":"medium","topic":"math","explanation":"Basic addition","choices":[{"text":"6","is_correct": true},{"text":"5","is_correct": false}]}]',
        content_type='application/json'
    )
})
request.user = user
try:
    response = import_exam_questions(request, exam.pk)
    print('status', response.status_code)
    print(response.content.decode('utf-8', errors='replace'))
except Exception as exc:
    import traceback
    traceback.print_exc()
