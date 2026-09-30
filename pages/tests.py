from django.test import TestCase
from django.contrib.auth import get_user_model

from pages.models import Page


class GlobalSearchTests(TestCase):
    def test_global_search_returns_matching_page_results(self):
        Page.objects.create(
            title='Exam Results',
            slug='exam-results',
            content='View student performance and report card summaries.',
            is_published=True,
        )

        response = self.client.get('/search/', {'q': 'exam results'})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertTrue(any(item['title'] == 'Exam Results' for item in data['results']))

    def test_global_search_includes_admin_scheme_approval_for_staff(self):
        user = get_user_model().objects.create_user(username='admin', password='password', is_staff=True)
        self.client.force_login(user)

        response = self.client.get('/search/', {'q': 'scheme'})

        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertTrue(any(
            item['url'] == '/teachers/admin/schemes/'
            for item in results
        ))

    def test_global_search_includes_teacher_schemes_for_teacher(self):
        user = get_user_model().objects.create_user(username='teacher', password='password')
        self.client.force_login(user)

        from school_classes.models import Teacher
        Teacher.objects.create(user=user)

        response = self.client.get('/search/', {'q': 'scheme'})

        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertTrue(any(
            item['url'] == '/teachers/schemes/'
            for item in results
        ))

    def test_global_search_includes_exam_review_for_admin(self):
        user = get_user_model().objects.create_user(username='exam-admin', password='password', is_staff=True)
        self.client.force_login(user)

        response = self.client.get('/search/', {'q': 'exam'})

        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertTrue(any(
            item['url'] == '/exams/admin/exam-papers/'
            for item in results
        ))

    def test_global_search_includes_exam_papers_for_teacher(self):
        user = get_user_model().objects.create_user(username='exam-teacher', password='password')
        self.client.force_login(user)

        from school_classes.models import Teacher
        Teacher.objects.create(user=user)

        response = self.client.get('/search/', {'q': 'exam'})

        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertTrue(any(
            item['url'] == '/exams/exam-papers/'
            for item in results
        ))


class HomepageTests(TestCase):
    def test_published_homepage_updates_render_inside_the_content_block(self):
        Page.objects.create(
            title='Term Dates',
            slug='term-dates',
            content='The new term begins soon.',
            is_published=True,
            show_on_homepage=True,
        )

        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="homepage-updates"')
        self.assertContains(response, 'Term Dates')
        self.assertContains(response, 'href="/students/apply/"')
        self.assertNotContains(response, 'href="/apply/"')
        self.assertContains(response, 'id="pageLoadStatus"')
        self.assertContains(response, 'role="status"')

    def test_named_routes_are_searchable_without_handwritten_keywords(self):
        from pages.views import _named_route_results

        routes = _named_route_results()

        self.assertTrue(any(
            item['url'] == '/exams/admin/exam-papers/' and 'admin_exam_paper_list' in item['keywords'][0]
            for item in routes
        ))
