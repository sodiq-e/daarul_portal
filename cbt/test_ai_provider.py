import unittest
from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase

from cbt.ai_provider import generate_ai_questions


class AIProviderTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_generate_ai_questions_uses_groq_when_available(self):
        response_text = """
        [
          {
            "prompt": "What is the capital of Nigeria?",
            "question_type": "mcq",
            "mark_value": 1.0,
            "topic": "Geography",
            "difficulty": "easy",
            "explanation": "Lagos is not the capital. Abuja is the capital of Nigeria.",
            "choices": [
              {"text": "Abuja", "is_correct": true, "order": 0},
              {"text": "Lagos", "is_correct": false, "order": 1},
              {"text": "Kano", "is_correct": false, "order": 2},
              {"text": "Port Harcourt", "is_correct": false, "order": 3}
            ]
          }
        ]
        """

        with patch('cbt.ai_provider.generate_with_groq', return_value=response_text) as groq_mock, \
             patch('cbt.ai_provider.generate_with_gemini') as gemini_mock:
            questions = generate_ai_questions(prompt='Generate one question')

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['prompt'], 'What is the capital of Nigeria?')
        groq_mock.assert_called_once()
        gemini_mock.assert_not_called()

    def test_generate_ai_questions_falls_back_to_gemini_on_groq_failure(self):
        response_text = """
        [
          {
            "prompt": "Which sentence is grammatically correct?",
            "question_type": "mcq",
            "mark_value": 1.0,
            "topic": "Grammar",
            "difficulty": "medium",
            "explanation": "This sentence uses the correct verb tense.",
            "choices": [
              {"text": "She go to school every day.", "is_correct": false, "order": 0},
              {"text": "She goes to school every day.", "is_correct": true, "order": 1},
              {"text": "She going to school every day.", "is_correct": false, "order": 2},
              {"text": "She gone to school every day.", "is_correct": false, "order": 3}
            ]
          }
        ]
        """

        with patch('cbt.ai_provider.generate_with_groq', side_effect=RuntimeError('Groq timeout')) as groq_mock, \
             patch('cbt.ai_provider.generate_with_gemini', return_value=response_text) as gemini_mock:
            questions = generate_ai_questions(prompt='Generate one grammar question')

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['topic'], 'Grammar')
        groq_mock.assert_called_once()
        gemini_mock.assert_called_once()

    def test_generate_ai_questions_raises_when_all_providers_fail(self):
        with patch('cbt.ai_provider.generate_with_groq', side_effect=RuntimeError('Groq unavailable')) as groq_mock, \
             patch('cbt.ai_provider.generate_with_gemini', side_effect=RuntimeError('Gemini unavailable')) as gemini_mock:
            with self.assertRaises(RuntimeError) as ctx:
                generate_ai_questions(prompt='Generate one invalid question prompt')

        self.assertIn('Both AI providers failed', str(ctx.exception))
        groq_mock.assert_called_once()
        gemini_mock.assert_called_once()

    def test_generate_ai_questions_rejects_invalid_payload(self):
        invalid_response = """
        Here is the answer:
        ```json
        [{"prompt": "", "question_type": "mcq", "mark_value": 1.0, "difficulty": "easy", "explanation": "", "choices": [{"text": "A", "is_correct": true, "order": 0}, {"text": "B", "is_correct": false, "order": 1}]}]
        ```
        """
        fallback_response = """
        [
          {
            "prompt": "What is the capital of Lagos?",
            "question_type": "mcq",
            "mark_value": 1.0,
            "topic": "Geography",
            "difficulty": "easy",
            "explanation": "Lagos is a city in Nigeria.",
            "choices": [
              {"text": "Abuja", "is_correct": false, "order": 0},
              {"text": "Lagos", "is_correct": true, "order": 1},
              {"text": "Kano", "is_correct": false, "order": 2},
              {"text": "Port Harcourt", "is_correct": false, "order": 3}
            ]
          }
        ]
        """

        with patch('cbt.ai_provider.generate_with_groq', return_value=invalid_response), \
             patch('cbt.ai_provider.generate_with_gemini', return_value=fallback_response) as gemini_mock:
            questions = generate_ai_questions(prompt='Generate invalid payload')

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['prompt'], 'What is the capital of Lagos?')
        gemini_mock.assert_called_once()


if __name__ == '__main__':
    unittest.main()
