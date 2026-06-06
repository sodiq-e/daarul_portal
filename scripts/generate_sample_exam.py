import os
import sys
import django

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daarul_portal.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from exams.models import ExamPaper, ExamSection, Question, QuestionOption, Subject, Term
from school_classes.models import SchoolClasses

def create_sample():
    User = get_user_model()
    teacher = User.objects.filter(is_superuser=True).first()
    if not teacher:
        teacher = User.objects.create(username='sample_teacher')

    school_class, _ = SchoolClasses.objects.get_or_create(class_name='Sample Class')
    subject, _ = Subject.objects.get_or_create(name='Sample Subject')
    term, _ = Term.objects.get_or_create(name='first', academic_year='2025/2026', display_name='First Term')

    ep = ExamPaper.objects.create(
        subject=subject,
        school_class=school_class,
        teacher=teacher,
        term=term,
        academic_session='2025/2026',
        duration='1 Hour',
        total_marks=50,
        instructions='Answer all questions.'
    )

    # Section 1 - Objective
    s1 = ExamSection.objects.create(exam=ep, title='Section A', section_type='objective', instruction='Choose the best answer', marks_allocation=30, order=1)
    q1 = Question.objects.create(section=s1, question_text='What is 2+2?', marks=1, order=1, question_type='objective', correct_answer='A')
    QuestionOption.objects.create(question=q1, option_label='A', option_text='4')
    QuestionOption.objects.create(question=q1, option_label='B', option_text='3')

    q2 = Question.objects.create(section=s1, question_text='What is 3+3?', marks=1, order=2, question_type='objective', correct_answer='B')
    QuestionOption.objects.create(question=q2, option_label='A', option_text='5')
    QuestionOption.objects.create(question=q2, option_label='B', option_text='6')

    # Section 2 - Theory
    s2 = ExamSection.objects.create(exam=ep, title='Section B', section_type='theory', instruction='Answer in detail', marks_allocation=20, order=2)
    Question.objects.create(section=s2, question_text='Explain photosynthesis.', marks=10, order=1, question_type='theory')

    # Render print template
    try:
        html = render_to_string('exams/print_exam_paper.html', {'exam_paper': ep})
        out = os.path.join(ROOT, 'sample_exam_paper.html')
        with open(out, 'w', encoding='utf-8') as f:
            f.write(html)
        print('Sample exam paper rendered to', out)
    except Exception as e:
        print('Rendering failed:', e)

if __name__ == '__main__':
    create_sample()
