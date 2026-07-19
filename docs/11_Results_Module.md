# 11. Results Module

## Feature Overview
The results module is one of the most significant features in the system. It handles result entry, grading, report cards, term summaries, promotions, conduct, and publication.

## Core Features

### Results Home and Navigation
- Entry point: /results/
- View: results_home
- Template: templates/results/results_home.html

### Report Card Student Listing
- Entry point: /results/report-card/<class_id>/<term_id>/
- View: report_card_student_list
- Template: templates/results/report_card_student_list.html

Workflow:
1. The view loads the target class and term
2. It checks user permissions based on role and class assignment
3. It accepts optional GET filters for academic session, term, and student
4. It builds student lists and aggregates based on the selected filters
5. It renders a report-card listing with charts and summaries

Business logic details:
- Student results are filtered based on selected academic session, term, and student
- Student list is narrowed to students who have matching results or belong to the class
- Aggregated charts switch between subject, student, and term-based views depending on the selected filter
- Distinct chart colors are generated dynamically for chart rendering

### Results Entry and Calculation
- Models: StudentResult, TermResult, ResultTemplate, GradeScale
- Business logic: StudentResult.save() calculates total score, percentage, grade, remark, and grade point from test and exam scores
- Aggregation: TermResult.calculate_aggregates() computes the average percentage and overall grade for a term

### Promotions
- Entry point: promotion-related result views
- Models: Promotion
- Workflow: students are promoted from one class to another and the promotion is recorded

### Student Conduct and Comments
- Models: StudentConduct, ReportCardComment
- Purpose: supplement report cards with conduct and teacher comments

### Publication Workflow
- Result publication is handled by admin result views and the is_published flag on StudentResult
- Published results are visible to students or other authorized users

## Dependencies
- Depends on students, exams, school_classes, attendance, and settingsapp

## Validation Rules
- Scores use decimal validators
- Unique constraints prevent duplicate subject results per student/term/class subject
- Report card filters must resolve to existing records or clear gracefully

## Permission Checks
- Approved users only
- Admins see all classes
- Teachers see only their assigned classes
- Students can view their own class content

## Outputs
- HTML report card pages
- chart data rendered in the browser
- printable report card structures and broadsheet outputs
