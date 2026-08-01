#!/usr/bin/env python3
import os
import django
import json
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daarul_portal.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from cbt.models import CBTExam, AIRequestMetric
from exams.models import Subject
from cbt import views as cbt_views

User = get_user_model()
user, created = User.objects.get_or_create(username='ai_test_user', defaults={'is_staff': True, 'email': 'ai@example.com'})
if created:
    user.set_password('testpass')
    user.save()

# ensure a Subject exists for the exam
subject, _ = Subject.objects.get_or_create(name='Mathematics', defaults={'code': 'MATH'})

# create a test exam owned by this user
exam = CBTExam.objects.create(name='Test AI Exam', created_by=user, allow_ai_questions=True, subject=subject)

rf = RequestFactory()
req = rf.post('/', content_type='application/json', data=json.dumps({'topic': 'math', 'difficulty': 'medium', 'num_questions': 1}))
req.user = user

# add a session to the request to satisfy session usage
middleware = SessionMiddleware(lambda request: None)
middleware.process_request(req)
req.session.save()

print('Calling api_generate_ai_questions for exam id', exam.pk)
resp = cbt_views.api_generate_ai_questions(req, exam.pk)
print('Response status:', getattr(resp, 'status_code', None))
content = getattr(resp, 'content', b'')
try:
    print('Response body:', content.decode())
except Exception:
    print('Response body (raw):', content)

metrics = list(AIRequestMetric.objects.filter(exam=exam).values('request_type', 'status', 'error_code', 'latency_ms')[:10])
print('AIRequestMetric entries for exam:', metrics)
