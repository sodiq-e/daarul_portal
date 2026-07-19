# 12. CBT Module

## Feature Overview
The CBT module provides a computer-based testing experience with exam-taking, question-bank management, AI-assisted question generation, analytics, and student practice modes.

## Core Features

### Exam and Attempt Management
- Entry points: /cbt/, /student/cbt/, /teacher/cbt/
- Views: cbt/views.py and cbt/question_bank_views.py
- Models: CBTExam, CBTQuestion, CBTStudentAttempt, CBTAnswer, etc.
- Templates: cbt/templates/cbt/*

### Question Bank Management
- Teachers/admins can create and manage question banks
- Questions can be attached to exams or used for practice

### AI Question Generation
- The module integrates with Gemini through cbt/gemini_service.py and cbt/ai_provider.py
- Purpose: generate exam questions or question set content using an AI provider

### Student Exam Attempt Flow
1. Student opens a CBT exam
2. The system loads questions from the exam or question bank
3. The student answers questions
4. The attempt is recorded and scored
5. Results are presented back to the student or teacher

### Teacher Analytics
- Teacher-facing analytics pages summarize performance and attempt data

## Dependencies
- Depends on exams and students for class and subject data
- Depends on settingsapp for site-wide settings and email features

## Validation Rules
- Questions and options are expected to respect exam structure and marking logic
- Attempts are tracked per student and exam

## Permission Checks
- Student access is limited to their own attempts
- Teachers/admins can manage exams and view analytics

## Notes
The CBT module is one of the most feature-rich parts of the entire project and includes both assessment delivery and AI augmentation.
