# 02. Project Architecture

## Architectural Style
The project follows a Django MVC-style structure:
- Models define data entities and relationships
- Views process request/response logic
- Templates render HTML
- URLs route requests to views
- Forms validate and transform submitted data

## App-Level Architecture

### accounts
Responsible for authentication, account approval, and profile management.

### students
Responsible for student records, admission applications, student portal, permissions, and printable admission forms.

### school_classes
Responsible for classes, teachers, subject assignment, and scheme-of-work workflows.

### exams
Responsible for subjects, exams, exam papers, questions, sections, approval workflow, and exports.

### results
Responsible for grading, report cards, term aggregates, promotions, student conduct, and publication flows.

### attendance
Responsible for attendance records, sessions, holidays, and teacher marking workflows.

### payroll
Responsible for school expenses, fee types, invoices, receipts/payments, and dashboard reports.

### communication
Responsible for public contact messages, admin replies, and portal messaging threads.

### settingsapp
Responsible for school settings, gallery, email service, and print verification helpers.

### pages
Responsible for custom pages and dynamic navigation.

### cbt
Responsible for computer-based testing, question banks, AI-generated questions, exam attempts, and analytics.

## Cross-App Dependencies
- results depends on students, exams, and school_classes
- exams depends on school_classes and settingsapp
- attendance depends on students, exams, and school_classes
- payroll depends on students and exams
- communication depends on settingsapp email helpers
- cbt depends on exams and students
- accounts depends on the profile and user-approval model

## Request Flow Example
1. User requests a page via URL
2. Django resolves the URL pattern
3. View checks authentication and authorization
4. View loads required model instances
5. Business logic applies validation and calculations
6. Template is rendered with context data
7. Response is returned to the browser or download handler

## Template Architecture
- Shared base template provides navigation, theme hooks, and layout utilities
- Module-specific templates extend or use the base layout
- Some pages render PDFs or print-friendly layouts

## Static and Media Architecture
- Static files are served from /static/ and collected into /staticfiles/
- Uploaded media files are served from /media/
- Settings support local and deployment environments
