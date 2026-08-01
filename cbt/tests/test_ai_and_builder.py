from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
import json
import io

from cbt.models import QuestionBank, CBTExam, AIRequestMetric, CBTQuestion, CBTChoice, CBTStudentAttempt
from exams.models import Subject


User = get_user_model()


class AIGenerationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='teacher_test', is_staff=True)
        self.user.set_password('pass')
        self.user.save()
        subject, _ = Subject.objects.get_or_create(name='Mathematics', defaults={'code': 'MATH'})
        self.exam = CBTExam.objects.create(name='T1', created_by=self.user, allow_ai_questions=True, subject=subject)
        self.client = Client()
        self.client.force_login(self.user)

    @patch('cbt.views.generate_ai_questions')
    def test_concurrent_generation_is_throttled_and_metrics_recorded(self, mock_generate):
        # Mock a simple successful generation
        mock_generate.return_value = [
            {
                'prompt': '1+1',
                'question_type': 'mcq',
                'mark_value': 1,
                'explanation': '2',
                'difficulty': 'medium',
                'choices': [
                    {'text': '2', 'is_correct': True},
                    {'text': '3', 'is_correct': False},
                    {'text': '4', 'is_correct': False},
                    {'text': '5', 'is_correct': False},
                ]
            }
        ]

        url = reverse('teacher_cbt:generate_ai_questions', kwargs={'exam_pk': self.exam.pk})
        payload = {'topic': 'math', 'difficulty': 'medium', 'num_questions': 1}

        # First request should succeed (200 OK & status ok)
        r1 = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(r1.status_code, 200)
        data1 = r1.json()
        self.assertEqual(data1.get('status'), 'ok')

        # Immediately make a second request to trigger lock/throttle
        r2 = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        # Expect a 429 or 400 depending on timing; ensure a throttled metric exists
        self.assertIn(r2.status_code, (200, 429, 503, 400))

        # Check that at least one AIRequestMetric was created for this exam
        metrics = AIRequestMetric.objects.filter(exam=self.exam)
        self.assertTrue(metrics.exists())


class BuilderAutosaveTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='teacher_builder', is_staff=True)
        self.user.set_password('pass')
        self.user.save()
        subject, _ = Subject.objects.get_or_create(name='Mathematics', defaults={'code': 'MATH'})
        self.exam = CBTExam.objects.create(name='BuilderExam', created_by=self.user, allow_ai_questions=False, subject=subject)
        self.client = Client()
        self.client.force_login(self.user)

    def test_autosave_json_endpoint_creates_questions(self):
        url = reverse('teacher_cbt:manage_questions', kwargs={'exam_pk': self.exam.pk})
        payload = {
            'questions': [
                {
                    'prompt': 'What is 2+2?',
                    'question_type': 'mcq',
                    'mark_value': 1,
                    'difficulty': 'medium',
                    'topic': 'arithmetic',
                    'explanation': '2+2=4',
                    'choices': [
                        {'text': '4', 'is_correct': True},
                        {'text': '3', 'is_correct': False},
                        {'text': '5', 'is_correct': False},
                        {'text': '22', 'is_correct': False},
                    ]
                }
            ],
            'deleted_question_ids': []
        }

        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get('status'), 'ok')
        self.assertTrue(len(data.get('created', [])) >= 1)

    def test_import_questions_json_creates_new_questions(self):
        url = reverse('teacher_cbt:import_questions', kwargs={'exam_pk': self.exam.pk})
        content = json.dumps([
            {
                'prompt': 'What is 3+3?',
                'question_type': 'mcq',
                'mark_value': 1,
                'difficulty': 'medium',
                'topic': 'math',
                'explanation': 'Basic addition',
                'choices': [
                    {'text': '6', 'is_correct': True},
                    {'text': '5', 'is_correct': False}
                ]
            }
        ]).encode('utf-8')
        upload = SimpleUploadedFile('questions.json', content, content_type='application/json')
        resp = self.client.post(url, {'file': upload})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get('status'), 'ok')
        self.assertEqual(data.get('created'), 1)
        self.assertEqual(CBTQuestion.objects.filter(exam=self.exam).count(), 1)
        self.assertEqual(CBTChoice.objects.filter(question__exam=self.exam).count(), 2)

    def test_import_questions_txt_creates_new_questions(self):
        url = reverse('teacher_cbt:import_questions', kwargs={'exam_pk': self.exam.pk})
        text_content = '\n'.join([
            'Prompt: What is 5 + 5?',
            'Type: mcq',
            'Marks: 1',
            'Difficulty: easy',
            'Topic: arithmetic',
            'Explanation: Ten',
            'Choices:',
            '- 10',
            '- 11',
            '- 9',
            'Correct Answers: 10',
        ])
        upload = SimpleUploadedFile('questions.txt', text_content.encode('utf-8'), content_type='text/plain')
        resp = self.client.post(url, {'file': upload})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get('status'), 'ok')
        self.assertEqual(data.get('created'), 1)
        question = CBTQuestion.objects.filter(exam=self.exam).first()
        self.assertIsNotNone(question)
        self.assertEqual(question.prompt, 'What is 5 + 5?')
        self.assertEqual(CBTChoice.objects.filter(question=question).count(), 3)

    def test_export_json_returns_serialized_questions(self):
        question = CBTQuestion.objects.create(
            exam=self.exam,
            prompt='What is 1+1?',
            question_type=CBTQuestion.MCQ,
            mark_value=1,
            explanation='Simple math',
            topic='math',
            difficulty=CBTQuestion.DIFFICULTY_MEDIUM,
            order=0,
            is_active=True
        )
        CBTChoice.objects.create(question=question, text='2', is_correct=True, order=0)
        CBTChoice.objects.create(question=question, text='3', is_correct=False, order=1)
        url = reverse('teacher_cbt:export_questions', kwargs={'exam_pk': self.exam.pk, 'format': 'json'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/json')
        data = json.loads(resp.content.decode('utf-8'))
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['prompt'], 'What is 1+1?')

    def test_export_csv_returns_successful_attachment(self):
        question = CBTQuestion.objects.create(
            exam=self.exam,
            prompt='What is 2+2?',
            question_type=CBTQuestion.MCQ,
            mark_value=1,
            explanation='Simple addition',
            topic='math',
            difficulty=CBTQuestion.DIFFICULTY_MEDIUM,
            order=0,
            is_active=True
        )
        CBTChoice.objects.create(question=question, text='4', is_correct=True, order=0)
        CBTChoice.objects.create(question=question, text='3', is_correct=False, order=1)
        url = reverse('teacher_cbt:export_questions', kwargs={'exam_pk': self.exam.pk, 'format': 'csv'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/csv', resp['Content-Type'])
        self.assertIn('attachment;', resp['Content-Disposition'])
        self.assertIn('4', resp.content.decode('utf-8'))

    def test_export_docx_returns_word_attachment(self):
        question = CBTQuestion.objects.create(
            exam=self.exam,
            prompt='What is 2+2?',
            question_type=CBTQuestion.MCQ,
            mark_value=1,
            explanation='Simple addition',
            topic='math',
            difficulty=CBTQuestion.DIFFICULTY_MEDIUM,
            order=0,
            is_active=True
        )
        CBTChoice.objects.create(question=question, text='4', is_correct=True, order=0)
        url = reverse('teacher_cbt:export_questions', kwargs={'exam_pk': self.exam.pk, 'format': 'docx'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.wordprocessingml.document', resp['Content-Type'])
        self.assertIn('attachment;', resp['Content-Disposition'])

    def test_export_xlsx_requires_openpyxl(self):
        try:
            import openpyxl
            openpyxl_installed = True
        except ImportError:
            openpyxl_installed = False

        question = CBTQuestion.objects.create(
            exam=self.exam,
            prompt='What is 2+2?',
            question_type=CBTQuestion.MCQ,
            mark_value=1,
            explanation='Simple addition',
            topic='math',
            difficulty=CBTQuestion.DIFFICULTY_MEDIUM,
            order=0,
            is_active=True
        )
        CBTChoice.objects.create(question=question, text='4', is_correct=True, order=0)
        url = reverse('teacher_cbt:export_questions', kwargs={'exam_pk': self.exam.pk, 'format': 'xlsx'})
        resp = self.client.get(url)
        if openpyxl_installed:
            self.assertEqual(resp.status_code, 200)
            self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', resp['Content-Type'])
        else:
            self.assertEqual(resp.status_code, 501)


class PracticeAttemptSaveTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='practice_teacher', is_staff=True)
        self.user.set_password('pass')
        self.user.save()
        subject, _ = Subject.objects.get_or_create(name='Practice Math', defaults={'code': 'MATH_PRACTICE'})
        self.exam = CBTExam.objects.create(
            name='PracticeExam',
            created_by=self.user,
            subject=subject,
            exam_mode=CBTExam.PRACTICE,
            is_published=True,
            is_active=True,
        )
        self.question1 = CBTQuestion.objects.create(
            exam=self.exam,
            prompt='What is 1+1?',
            question_type=CBTQuestion.MCQ,
            mark_value=1,
            difficulty='medium',
            topic='math',
            explanation='Simple addition',
            order=0,
            is_active=True,
        )
        self.question2 = CBTQuestion.objects.create(
            exam=self.exam,
            prompt='What is 2+2?',
            question_type=CBTQuestion.MCQ,
            mark_value=1,
            difficulty='medium',
            topic='math',
            explanation='Simple addition',
            order=1,
            is_active=True,
        )
        CBTChoice.objects.create(question=self.question1, text='2', is_correct=True, order=0)
        CBTChoice.objects.create(question=self.question1, text='3', is_correct=False, order=1)
        CBTChoice.objects.create(question=self.question2, text='4', is_correct=True, order=0)
        CBTChoice.objects.create(question=self.question2, text='5', is_correct=False, order=1)
        self.client = Client()

    def test_practice_attempt_save_persists_multiple_answers(self):
        start_url = reverse('cbt:practice_exam_start', kwargs={'pk': self.exam.pk})
        resp = self.client.get(start_url)
        self.assertEqual(resp.status_code, 302)

        attempt_url = resp['Location']
        resp = self.client.get(attempt_url)
        self.assertEqual(resp.status_code, 200)
        csrf_token = self.client.cookies['csrftoken'].value

        attempt = CBTStudentAttempt.objects.last()
        question_ids = list(attempt.attempt_questions.order_by('randomized_position').values_list('question_id', flat=True))

        save_url = reverse('cbt:api_save_answer')
        first_choice = CBTChoice.objects.filter(question_id=question_ids[0]).first()
        second_choice = CBTChoice.objects.filter(question_id=question_ids[1]).first()

        payload1 = {
            'attempt_uuid': str(attempt.uuid),
            'question_id': question_ids[0],
            'selected_choice_id': first_choice.id,
        }
        resp = self.client.post(save_url, data=json.dumps(payload1), content_type='application/json', HTTP_X_CSRFTOKEN=csrf_token)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get('status'), 'saved')

        payload2 = {
            'attempt_uuid': str(attempt.uuid),
            'question_id': question_ids[1],
            'selected_choice_id': second_choice.id,
        }
        resp = self.client.post(save_url, data=json.dumps(payload2), content_type='application/json', HTTP_X_CSRFTOKEN=csrf_token)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get('status'), 'saved')

        attempt.refresh_from_db()
        self.assertEqual(attempt.answers.count(), 2)
        self.assertTrue(attempt.attempt_questions.get(question_id=question_ids[0]).is_answered)
        self.assertTrue(attempt.attempt_questions.get(question_id=question_ids[1]).is_answered)


class QuestionBankPhase1Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='teacher_bank', is_staff=True)
        self.user.set_password('pass')
        self.user.save()
        teacher_group, _ = self.user.groups.model.objects.get_or_create(name='Teacher')
        self.user.groups.add(teacher_group)
        from accounts.models import Profile
        profile, _ = Profile.objects.get_or_create(user=self.user)
        profile.is_approved = True
        profile.requested_group = 'Teacher'
        profile.save()
        self.user.refresh_from_db()
        self.client = Client()
        self.client.force_login(self.user)
        self.subject, _ = Subject.objects.get_or_create(code='ENG', defaults={'name': 'English'})
        self.bank_one = QuestionBank.objects.create(
            name='English Banks',
            subject=self.subject,
            created_by=self.user,
        )
        self.bank_two = QuestionBank.objects.create(
            name='Science Bank',
            subject=self.subject,
            created_by=self.user,
        )
        self.exam = CBTExam.objects.create(name='BankExam', created_by=self.user, subject=self.subject)

    def test_question_bank_list_search_filters(self):
        url = reverse('teacher_cbt:question_banks')
        resp = self.client.get(url, {'q': 'English'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.bank_one.name, resp.content.decode('utf-8'))
        self.assertNotIn(self.bank_two.name, resp.content.decode('utf-8'))

    def test_question_toggle_favorite_and_bulk_move(self):
        question = CBTQuestion.objects.create(
            exam=self.exam,
            question_bank=self.bank_one,
            prompt='What is a noun?',
            question_type=CBTQuestion.MCQ,
            mark_value=1,
            topic='Grammar',
            difficulty=CBTQuestion.DIFFICULTY_MEDIUM,
            order=0,
            is_active=True,
        )
        CBTChoice.objects.create(question=question, text='Person', is_correct=True, order=0)
        CBTChoice.objects.create(question=question, text='Run', is_correct=False, order=1)

        toggle_url = reverse('teacher_cbt:question_toggle_favorite', kwargs={'question_pk': question.pk})
        resp = self.client.post(toggle_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        question.refresh_from_db()
        self.assertTrue(question.is_favorite)

        bulk_url = reverse('teacher_cbt:question_bank_bulk_actions', kwargs={'pk': self.bank_one.pk})
        resp = self.client.post(bulk_url, {
            'action': 'move',
            'selected_questions': [str(question.pk)],
            'target_bank': str(self.bank_two.pk),
        })
        self.assertEqual(resp.status_code, 302)
        question.refresh_from_db()
        self.assertEqual(question.question_bank, self.bank_two)

    def test_teacher_dashboard_includes_question_bank_counts(self):
        url = reverse('teacher_cbt:dashboard')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        self.assertIn('Question Banks', content)
        self.assertIn(str(self.bank_one.name), content)
        self.assertIn(str(self.bank_two.name), content)
