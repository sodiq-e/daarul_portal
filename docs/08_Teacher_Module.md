# 08. Teacher Module

## Feature Overview
The teacher module includes teacher profiles, class assignments, permissions, schemes of work, attendance marking, exam paper creation, and results review.

## Core Features

### Teacher Profiles and Assignment
- Models: school_classes.Teacher, school_classes.ClassTeacher
- Views: teacher-related views embedded in school_classes and exams modules
- Permission: approved teacher accounts

Business logic:
- Teachers are assigned to classes and subjects
- Class Teacher assignments define teacher authority over a class
- Permissions can be granted or denied per teacher

### Scheme of Work
- Models: SchemeOfWork, SchemeWeek
- Views: teacher scheme views in school_classes or template-driven views
- Templates: templates/teachers/scheme/*
- Workflow:
  1. Teacher creates a scheme of work
  2. Weeks are added and completed
  3. Teacher submits for approval
  4. Admin acknowledges and approves weekly completion

### Attendance Marking
- Entry point: teacher attendance views
- View: TeacherAttendanceMarkView
- Template: templates/teachers/attendance/mark_attendance.html
- Permission: teacher must have mark_attendance permission

Workflow:
1. Teacher selects a class and date
2. The system checks holiday and term restrictions
3. Student attendance records are loaded or created
4. Teacher submits attendance data

### Exam Paper Creation
- Entry point: /exams/teacher/
- Views: TeacherExamPaperListView, TeacherExamPaperDetailView, TeacherExamPaperCreateView, TeacherExamPaperUpdateView
- Model: ExamPaper
- Templates: exams/templates/exams/teacher_exam_list.html and related templates

Workflow:
1. Teacher drafts an exam paper
2. Sections and questions are created
3. Paper is submitted for review
4. Admin approves or rejects it

### Results Editing
- Teacher access to edit results exists through results-related templates and views
- Views: teacher results pages in results/views.py or teacher-specific templates
- Permission: teacher-specific permissions and class assignment

## Dependencies
- Depends on school_classes for class assignments and permissions
- Depends on exams for subject and exam paper workflows
- Depends on results for result editing and report-card content
- Depends on attendance for marking class attendance

## Validation Rules
- Scheme weeks are keyed by scheme and week number
- Permission checks are enforced before each action
- Attendance dates may be restricted by configured academic term dates
