# 07. Student Module

## Feature Overview
The student module covers student records, application workflow, portal access, and student-facing features.

## Core Features

### Student Record Management
- Entry point: /students/
- Views: StudentListView, StudentDetailView, StudentCreateView, StudentUpdateView, StudentDeleteView
- Models: Student
- Templates: templates/students/student_list.html, student_detail.html, student_form.html
- Permission: approved staff/teacher/admin accounts

Workflow:
1. Staff user opens the student list view
2. Student records are loaded from the Student model
3. CRUD actions are available based on permission
4. Student class and status fields are updated as needed

### Student Application Workflow
- Entry point: /students/apply/ or related student application routes
- Views: StudentApplicationCreateView, StudentApplicationListView, StudentApplicationDetailView, StudentApplicationUpdateView
- Models: StudentApplication, AdmissionFormField, AdmissionFormResponse
- Templates: templates/students/student_application_modern.html, student_application_list.html, student_application_detail.html
- Permission: public submission for creation; staff review for list/detail/update

Workflow:
1. Applicant submits application data
2. Application is stored with pending status
3. Staff reviews the application
4. Reviewer can accept or reject the application
5. The application can later become a student record

### Student Portal
- Entry point: /students/portal/ (via student URLs)
- Views: StudentDashboardView and related portal views
- Templates: templates/students/portal/*
- Models: Student, StudentInvoice, StudentResult, StudentConduct

Features:
- dashboard
- profile
- results
- fees
- attendance
- announcements
- timetable
- contact teachers

### Admission Application PDF
- Entry point: print view for application detail
- View: print_admission_application
- Template: templates/students/admission_application_print.html
- Output: PDF when weasyprint is available, otherwise HTML response

## Dependencies
- Depends on school_classes for class references
- Depends on results for report card data in the student portal
- Depends on payroll for invoices and balances
- Depends on communication for teacher contact features

## Validation Rules
- Admission number must be unique
- Form field responses are stored for dynamic fields
- Status choices are constrained to allowed values

## Permission Checks
- Staff/teacher/admin can manage records
- Public applicants can submit an application
- Students can access their own portal content
