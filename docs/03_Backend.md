# 03. Backend Documentation

## Backend Framework
The backend is implemented using Django with class-based and function-based views. The project uses standard Django ORM, auth, sessions, messages, forms, templates, and file handling.

## Core Backend Modules

### Authentication and Profiles
Location: accounts/views.py, accounts/models.py

Features:
- student signup
- login with approval validation
- password reset
- user profile update

Business logic:
- User submits signup form
- Profile is created through the account flow
- Admin approval changes the profile to approved
- Profile approval automatically activates the user and assigns the requested group

Permission checks:
- Only approved users can access protected areas
- Login view denies inactive or unapproved users

### Student Management
Location: students/views.py, students/models.py

Features:
- CRUD for student records
- admission applications
- printable application PDF generation
- student portal dashboard
- permissions for student portal features

Business logic:
- Student records are created and linked to a class and optional user account
- Applications are reviewed, accepted, or rejected
- PDF export renders a printable admissions form

Validation rules:
- Admission numbers are unique
- Application and student forms are validated through Django forms
- Some workflow fields are optional and some are required

### Exams and Question Bank
Location: exams/views.py, exams/models.py

Features:
- create/manage subjects
- create/manage exams
- create exam papers and sections
- create questions and options
- approval workflow for exam papers
- export/preview support

Business logic:
- Teachers create exam papers and submit them
- Admins review and approve or reject them
- Questions are grouped into sections with ordering and marking information

Database operations:
- create/update/delete for exam-related records
- approval log entries are written for each action

### Results and Report Cards
Location: results/views.py, results/models.py

Features:
- result entry and calculation
- report card generation
- aggregate term results
- promotions
- student conduct and comments

Business logic:
- StudentResult.save() computes total score, percentage, grade, and remark using the configured grade scale
- TermResult.calculate_aggregates() derives summary metrics from individual subject results
- Report cards can be filtered by class, term, academic session, and student

Validation rules:
- Scores are constrained by validators in the models
- Unique constraints prevent duplicate subject entries per student/term/class

Permission checks:
- Staff/teacher/admin access is enforced based on profile approval and group membership

### Attendance
Location: attendance/views.py, attendance/models.py

Features:
- mark attendance by class and date
- holiday handling
- term-based date restrictions
- attendance reporting

Business logic:
- Teachers choose a class and date
- The system checks whether the date falls on a holiday or outside configured term dates
- Records are stored per student and date

### Payroll
Location: payroll/views.py, payroll/models.py

Features:
- manage school expenses and fee types
- create invoices and payments
- print invoices and receipts
- payroll dashboard dashboards

Business logic:
- Invoices are aggregated by student and term
- Payment balances and outstanding statuses are calculated from invoice data

### Communication
Location: communication/views.py, communication/models.py

Features:
- public contact form
- admin replies via email or portal messages
- portal inbox and threading

Business logic:
- Contact messages are stored and emailed to the school
- Admin replies can be sent by email or as portal messages

### Settings and Content
Location: settingsapp/views.py, settingsapp/models.py

Features:
- manage school settings
- manage gallery images
- publish custom pages and page themes

## Helper and Service Modules
- settingsapp/email_service.py: sends school contact and confirmation emails
- settingsapp/print_utils.py: print helpers
- cbt/gemini_service.py: AI integration for question generation
- exams/export_utils.py: exam export helpers

## Error Handling Patterns
- Views commonly use messages for user feedback
- Some views redirect home on permission denial
- PDF generation falls back to HTML when weasyprint is unavailable
- Several helper functions include defensive checks for missing profiles or permissions

## Background Database Operations
- Several models implement save-time calculation logic
- Some workflows create related records automatically after creation
- Aggregations are recalculated in the view layer and in model helper methods
