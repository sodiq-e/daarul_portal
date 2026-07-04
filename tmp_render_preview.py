import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daarul_portal.settings')
import django
django.setup()
from django.template.loader import render_to_string
from exams.models import ExamPaper
from django.contrib.auth import get_user_model
from django.conf import settings
from django.http import HttpRequest
import traceback

settings.ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']

exam = ExamPaper.objects.first()
print('exam', exam)
req = HttpRequest()
req.user = get_user_model().objects.filter(is_superuser=True).first()
ctx = {'exam': exam, 'sections_data': [], 'can_submit': False, 'can_approve': False, 'font_size': '12pt'}

try:
    html = render_to_string('exams/exam_paper_preview.html', ctx, request=req)
    print(html[:5000])
except Exception as exc:
    print(type(exc).__name__, exc)
    traceback.print_exc()
