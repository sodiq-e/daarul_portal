# 01. Project Overview

## Purpose
This repository implements a Django-based school portal for managing student admissions, class administration, exams, results, attendance, payroll, communications, and a CBT/exam system.

## Scope
The application supports:
- public-facing school content and contact forms
- student admission and application workflows
- student and teacher portals
- exam paper creation and approval
- results entry, publication, and report card generation
- attendance tracking
- payroll and fees management
- communication between admins and users
- AI-assisted question generation in the CBT module

## Primary Actors
- Public visitors
- Student applicants
- Students
- Teachers
- Staff
- Administrators
- Parents/guardians (indirectly through student profiles and contact workflows)

## Core Technology Stack
- Python / Django
- SQLite for local development
- Django templates with Bootstrap styling
- Django REST Framework installed
- Chart.js for results charts
- CKEditor for exam paper and question content
- WhiteNoise for static files
- WeasyPrint for PDF generation where available

## Main Entry Points
- Admin site: /admin/
- Login: /login/
- Student portal routes: /students/
- Results routes: /results/
- Exams routes: /exams/
- Attendance routes: /attendance/
- Payroll routes: /payroll/
- Communication routes: /announcements/, /contact/, /messages/
- CBT routes: /cbt/, /student/cbt/, /teacher/cbt/

## Notable Architectural Characteristics
- Modular app-based architecture
- Shared templates directory and shared base template
- Custom context processors for school settings, navigation, and messaging
- Mixed function-based and class-based views
- Model-centric business logic with several save hooks and aggregate calculations
