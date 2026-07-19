# 05. Database and Data Model

## Database Engine
The project uses SQLite for local development through the configured database file db.sqlite3.

## Core Entities

### accounts.Profile
Represents account approval and role request state for each Django user.

Relationships:
- OneToOne to User
- optional approved_by foreign key to User

Key business logic:
- If profile is approved, the user is activated and assigned to the requested group.

### students.Student
Represents a student record.

Relationships:
- ForeignKey to SchoolClasses
- Optional OneToOne to User
- Reverse relationships to StudentResult, TermResult, StudentConduct, StudentInvoice, etc.

### students.StudentApplication
Represents a student admission application.

Relationships:
- ForeignKey to SchoolClasses as desired_class
- ForeignKey to submitting/reviewing user
- Related admission form responses

### exams.Term
Represents an academic term.

### exams.Subject
Represents a school subject.

### exams.ClassSubject
Maps a subject to a class.

### exams.ExamPaper / ExamSection / Question / QuestionOption
Represents exam paper creation and structure.

### results.ResultTemplate / GradeScale / StudentResult / TermResult
Represents report-card templates, grading, per-subject results, and term aggregate results.

### school_classes.SchoolClasses / Teacher / ClassTeacher / SchemeOfWork / SchemeWeek / TeacherPermission
Represents classes, teacher assignment, scheme approval, and teacher permissions.

### attendance.AttendanceRecord / AttendanceSession / AttendanceHoliday / AttendanceSettings
Represents attendance recording and rule configuration.

### payroll.SchoolExpense / SchoolFee / StudentInvoice / StudentPayment / Payslip / SalaryComponent
Represents financial operations.

### communication.Message / PortalThread / PortalMessage
Represents public contact messages and portal conversations.

### settingsapp.SchoolSettings / GalleryImage / PageTheme
Represents site customization and gallery content.

## Important Relationships
- Student belongs to a SchoolClasses instance
- StudentResult belongs to a Student, ClassSubject, Term, and ResultTemplate
- TermResult belongs to a Student and Term
- AttendanceRecord belongs to a Student, SchoolClasses, and Term if configured
- StudentInvoice belongs to a Student, Fee type, and Term
- ExamPaper belongs to a Subject, SchoolClass, Teacher, and Term
- ClassTeacher links Teacher to SchoolClasses and Subject

## Validation and Integrity Rules
- Unique constraints exist for many natural compound keys
- Some fields are required while others are optional
- Several models use validators for numeric ranges

## Database Operations Observed in Views
- Create, update, delete operations through Django forms and generic views
- Aggregations via Avg, Sum, Min, Max, Count
- Bulk filtering and list generation via ORM querysets
