import os
import django
import json
import re
from django.test import Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daarul_portal.settings')
django.setup()
from django.contrib.auth import get_user_model
from exams.models import Subject
from cbt.models import CBTExam, CBTQuestion, CBTChoice, CBTStudentAttempt

User = get_user_model()
user, _ = User.objects.get_or_create(username='practice_user')
user.set_password('pass')
user.save()
subject, _ = Subject.objects.get_or_create(name='Math Repro', defaults={'code': 'MATH_REPRO'})
exam = CBTExam.objects.create(
    name='PracticeTest',
    created_by=user,
    subject=subject,
    exam_mode=CBTExam.PRACTICE,
    is_published=True,
    is_active=True,
)
q1 = CBTQuestion.objects.create(
    exam=exam,
    prompt='Q1',
    question_type='mcq',
    mark_value=1,
    difficulty='medium',
    topic='t',
    explanation='e',
    order=0,
    is_active=True,
)
q2 = CBTQuestion.objects.create(
    exam=exam,
    prompt='Q2',
    question_type='mcq',
    mark_value=1,
    difficulty='medium',
    topic='t',
    explanation='e',
    order=1,
    is_active=True,
)
for q, texts in [(q1, ['A', 'B', 'C', 'D']), (q2, ['W', 'X', 'Y', 'Z'])]:
    for i, t in enumerate(texts):
        CBTChoice.objects.create(question=q, text=t, is_correct=(i == 0), order=i)
from django.conf import settings
settings.ALLOWED_HOSTS.append('testserver')
client = Client()
client.cookies.clear()
from django.urls import reverse
url = reverse('cbt:practice_exam_start', kwargs={'pk': exam.pk})
resp = client.get(url, SERVER_NAME='localhost')
print('start', resp.status_code, resp.get('Location'))
# Ensure the session persists and we have CSRF token from a page render
attempt_url = '/cbt/attempt/{}/'.format(resp.url.split('/')[-2])
attempt_page = client.get(attempt_url, SERVER_NAME='localhost')
print('attempt page status', attempt_page.status_code)
print('attempt page cookies', client.cookies.items())
csrftoken = client.cookies.get('csrftoken')
print('csrftoken', csrftoken)
if not csrftoken:
    raise RuntimeError('No CSRF token available')

m = re.search(r'/attempt/([0-9a-fA-F-]+)/', resp.get('Location') or resp.url)
if not m:
    raise RuntimeError('No uuid in redirect')
uuid = m.group(1)
attempt = CBTStudentAttempt.objects.get(uuid=uuid)
qs = list(attempt.attempt_questions.all().order_by('randomized_position'))
print('questions count', len(qs))
print('questions', [aq.question.prompt for aq in qs])
answer1 = {
    'attempt_uuid': str(attempt.uuid),
    'question_id': qs[0].question.id,
    'selected_choice_id': qs[0].question.choices.first().id,
}
resp1 = client.post('/cbt/api/save-answer/', data=json.dumps(answer1), content_type='application/json', HTTP_X_CSRFTOKEN=csrftoken.value if csrftoken else '')
print('save1', resp1.status_code, resp1.content.decode('utf-8'), dict(resp1.headers))
answer2 = {
    'attempt_uuid': str(attempt.uuid),
    'question_id': qs[1].question.id,
    'selected_choice_id': qs[1].question.choices.first().id,
}
resp2 = client.post('/cbt/api/save-answer/', data=json.dumps(answer2), content_type='application/json', HTTP_X_CSRFTOKEN=csrftoken.value if csrftoken else '')
print('save2', resp2.status_code, resp2.content.decode('utf-8'), dict(resp2.headers))
print('answers count', attempt.answers.count())
for ans in attempt.answers.all():
    print(ans.question.prompt, ans.selected_choice.text if ans.selected_choice else None, ans.is_correct, ans.awarded_marks)
