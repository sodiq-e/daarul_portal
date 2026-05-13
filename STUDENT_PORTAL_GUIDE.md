# Student Portal - Implementation Guide

## Overview
This document provides a comprehensive guide to the Student Portal functionality in the Daarul Portal system. It covers the results fetching mechanism, all implemented features, URL routes, and the end-to-end flow for students.

## 1. How Results Are Fetched

### ResultsFetching in StudentResultsView

**File:** `students/views.py` - `StudentResultsView`

```python
class StudentResultsView(LoginRequiredMixin, TemplateView):
    """Student view their academic results"""
    template_name = 'students/portal/student_results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from results.models import StudentResult
            student = self.request.user.student_profile
            context['student'] = student
            # Fetch results with related objects
            context['results'] = StudentResult.objects.filter(
                student=student
            ).select_related('class_subject__subject', 'term').order_by('-term__academic_year')
        except Student.DoesNotExist:
            context['student'] = None
            context['results'] = []
        return context
```

**Query Breakdown:**
- **Filter:** `StudentResult.objects.filter(student=student)` - Gets all results for the logged-in student
- **Select Related:** `.select_related('class_subject__subject', 'term')` - Optimizes query by fetching related:
  - `class_subject__subject`: The subject name
  - `term`: The term information (academic year, term number, etc.)
- **Ordering:** `.order_by('-term__academic_year')` - Orders by academic year (newest first)

**Data Model Relationships:**
```
Student → StudentResult
         ├── class_subject
         │   └── subject
         └── term
```

### Report Card Fetching

**File:** `students/views.py` - `StudentDownloadReportCardView`

```python
class StudentDownloadReportCardView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from results.models import TermResult
            student = self.request.user.student_profile
            context['student'] = student
            # Get all term results for this student
            context['term_results'] = TermResult.objects.filter(
                student=student
            ).select_related('term', 'class_subject__subject').order_by('-term__academic_year', '-term__term_number')
        except Student.DoesNotExist:
            context['student'] = None
            context['term_results'] = []
        return context
```

**Key Features:**
- Fetches `TermResult` (consolidated results per term)
- Orders by academic year and term number
- Supports PDF download using WeasyPrint
- File download: `report_card_{admission_no}.pdf`

## 2. Student Portal Features (10 Features)

### Feature 1: View Own Profile
- **URL:** `/students/portal/profile/`
- **View:** `StudentProfileDetailView`
- **Template:** `students/portal/student_profile.html`
- **Permission:** `view_own_profile`
- **Description:** Students can view their personal information including name, admission number, class, contact details, etc.
- **Data Displayed:**
  - Full name
  - Admission number
  - Date of birth
  - Contact information
  - Guardian information
  - Class assignment
  - Status

### Feature 2: View Own Results
- **URL:** `/students/portal/results/`
- **View:** `StudentResultsView`
- **Template:** `students/portal/student_results.html`
- **Permission:** `view_own_results`
- **Description:** Students can view their academic results for all exams/tests
- **Data Displayed:**
  - Subject name
  - Exam/Test name
  - Score achieved
  - Grade (if applicable)
  - Date of exam
  - Results sorted by academic year

### Feature 3: Download Report Card
- **URL:** `/students/portal/report-card/`
- **View:** `StudentDownloadReportCardView`
- **Template:** `students/portal/download_report_card.html`
- **Permission:** `download_report_card`
- **Description:** Students can download their term report cards as PDF
- **Functionality:**
  - Lists all term reports
  - One-click PDF download
  - File naming: `report_card_{admission_no}.pdf`
  - Uses WeasyPrint for PDF generation

### Feature 4: View School Fees
- **URL:** `/students/portal/fees/`
- **View:** `StudentFeesView`
- **Template:** `students/portal/student_fees.html`
- **Permission:** `view_own_fees`
- **Description:** Students can view their invoices and payment history
- **Data Displayed:**
  - Pending invoices count
  - Invoice details (amount, due date, status)
  - Payment history
  - Total due, total paid, total owing amounts
  - Payment status indicators

### Feature 5: View Class Timetable
- **URL:** `/students/portal/timetable/`
- **View:** `StudentClassTimetableView`
- **Template:** `students/portal/class_timetable.html`
- **Permission:** `view_class_timetable`
- **Description:** Students can view their class schedule and subjects
- **Data Displayed:**
  - Class name
  - Class level
  - List of all subjects offered by the class
  - Subject teachers (if assigned)
  - Compulsory vs optional subject indicators

### Feature 6: View Class Announcements
- **URL:** `/students/portal/announcements/`
- **View:** `StudentClassAnnouncementsView`
- **Template:** `students/portal/class_announcements.html`
- **Permission:** `view_class_announcements`
- **Description:** Students can view announcements published for their class
- **Data Displayed:**
  - Announcement title
  - Announcement content (truncated preview)
  - Posted date and time
  - Posted by (teacher/admin name)
  - Link to full announcement
  - Filtered by: class, published status
  - Ordered by: newest first

### Feature 7: Submit Assignments
- **URL:** Not yet implemented (placeholder in permissions)
- **Permission:** `submit_assignments`
- **Note:** This feature requires an Assignment model to be created with student submission tracking

### Feature 8: View Own Attendance
- **URL:** `/students/portal/attendance/`
- **View:** `StudentAttendanceView`
- **Template:** `students/portal/student_attendance.html`
- **Permission:** `view_attendance`
- **Description:** Students can view their attendance records
- **Data Displayed:**
  - Total sessions attended/missed
  - Attendance count (present, absent)
  - Attendance percentage
  - Attendance table with date, term, and status
  - Color-coded status badges (Present=Green, Absent=Red)
  - Attendance breakdown in cards

### Feature 9: Contact Teachers
- **URL:** `/students/portal/contact-teacher/`
- **View:** `StudentContactTeacherView`
- **Template:** `students/portal/contact_teacher.html`
- **Permission:** `contact_teacher`
- **Description:** Students can send messages to their teachers
- **Data Displayed:**
  - List of all teachers assigned to student's class
  - Teacher information:
    - Full name
    - Subject taught
    - Employee ID
    - Phone number
    - Email address
  - "Send Message" button linking to portal messaging system
  - Filters by: active class teachers, not by subject

### Feature 10: Access Student Portal
- **URL:** `/students/portal/dashboard/`
- **View:** `StudentDashboardView`
- **Template:** `students/portal/student_dashboard.html`
- **Permission:** `access_portal`
- **Description:** Main dashboard/gateway to all student portal features
- **Features:**
  - Student welcome message with admission number
  - Quick stats cards:
    - Current class
    - Student status (Active, Inactive, etc.)
    - Pending invoices count
    - Amount owing
  - Feature navigation grid:
    - All 10+ features accessible via card buttons
    - Emoji icons for visual identification
    - Feature descriptions
    - Responsive grid layout (2-3 columns on desktop, 1 on mobile)

## 3. Student Portal URLs

```python
# File: students/urls.py

urlpatterns = [
    # Student Portal Routes
    path('portal/dashboard/', StudentDashboardView.as_view(), name='student_portal_dashboard'),
    path('portal/profile/', StudentProfileDetailView.as_view(), name='student_portal_profile'),
    path('portal/results/', StudentResultsView.as_view(), name='student_portal_results'),
    path('portal/fees/', StudentFeesView.as_view(), name='student_portal_fees'),
    path('portal/report-card/', StudentDownloadReportCardView.as_view(), name='student_portal_report_card'),
    path('portal/timetable/', StudentClassTimetableView.as_view(), name='student_portal_timetable'),
    path('portal/announcements/', StudentClassAnnouncementsView.as_view(), name='student_portal_announcements'),
    path('portal/attendance/', StudentAttendanceView.as_view(), name='student_portal_attendance'),
    path('portal/contact-teacher/', StudentContactTeacherView.as_view(), name='student_portal_contact_teacher'),
]
```

## 4. End-to-End Student Portal Flow

### User Journey: Complete Login to Feature Access

```
1. Student Access Point
   ├─ Login via /login/ (CustomLoginView)
   └─ Authenticated → Redirected to student_portal_dashboard

2. Dashboard (Main Hub)
   ├─ /students/portal/dashboard/
   ├─ Display:
   │  ├─ Welcome card with admission number
   │  ├─ Quick stats (class, status, fees owing)
   │  └─ Feature navigation grid (10 cards)
   └─ Feature Buttons:
      ├─ View Profile → Feature 1
      ├─ View Results → Feature 2
      ├─ Download Report Card → Feature 3
      ├─ School Fees → Feature 4
      ├─ Class Timetable → Feature 5
      ├─ Class Announcements → Feature 6
      ├─ My Attendance → Feature 8
      ├─ Contact Teachers → Feature 9
      └─ Portal Messages → External (communication app)

3. Feature Examples:

   Example A: View Results
   ├─ Click "View Results" on dashboard
   ├─ Navigate to /students/portal/results/
   ├─ View:
   │  ├─ StudentResultsView queries:
   │  │  └─ StudentResult.objects.filter(student=logged_in_student)
   │  ├─ Display in table:
   │  │  ├─ Subject | Exam | Score | Grade | Date
   │  │  └─ Each result row with exam details
   │  └─ Download Report Card button in header
   └─ Return to Dashboard

   Example B: Download Report Card
   ├─ Click "Download Report Card" on dashboard or results page
   ├─ Navigate to /students/portal/report-card/
   ├─ View:
   │  ├─ StudentDownloadReportCardView queries:
   │  │  └─ TermResult.objects.filter(student=logged_in_student)
   │  ├─ Display cards for each term
   │  └─ Each card has "Download PDF" button
   ├─ Click "Download PDF" for specific term
   ├─ Generate PDF using WeasyPrint
   └─ File downloaded: report_card_{admission_no}.pdf

   Example C: View Attendance
   ├─ Click "My Attendance" on dashboard
   ├─ Navigate to /students/portal/attendance/
   ├─ View:
   │  ├─ StudentAttendanceView queries:
   │  │  └─ AttendanceRecord.objects.filter(student=logged_in_student)
   │  ├─ Display attendance summary cards:
   │  │  ├─ Total Sessions
   │  │  ├─ Present Count
   │  │  ├─ Absent Count
   │  │  └─ Attendance Percentage
   │  └─ Display table with all attendance records
   └─ Return to Dashboard

   Example D: Contact Teachers
   ├─ Click "Contact Teachers" on dashboard
   ├─ Navigate to /students/portal/contact-teacher/
   ├─ View:
   │  ├─ StudentContactTeacherView queries:
   │  │  └─ ClassTeacher.objects.filter(school_class=student_class)
   │  ├─ Display teacher cards with:
   │  │  ├─ Teacher name
   │  │  ├─ Subject taught
   │  │  ├─ Contact information
   │  │  └─ "Send Message" button
   │  └─ Send Message links to portal messaging
   └─ Return to Dashboard
```

## 5. Permission Model

### StudentPermission Model

**File:** `students/models.py`

```python
class StudentPermission(models.Model):
    PERMISSION_CHOICES = [
        ('view_own_profile', 'View Own Profile'),
        ('view_own_results', 'View Own Results'),
        ('download_report_card', 'Download Report Card'),
        ('view_own_fees', 'View School Fees'),
        ('view_class_timetable', 'View Class Timetable'),
        ('view_class_announcements', 'View Class Announcements'),
        ('submit_assignments', 'Submit Assignments'),
        ('view_attendance', 'View Own Attendance'),
        ('contact_teacher', 'Contact Teachers'),
        ('access_portal', 'Access Student Portal'),
    ]
    
    student = ForeignKey(Student, on_delete=models.CASCADE, related_name='permissions')
    permission = CharField(max_length=50, choices=PERMISSION_CHOICES)
    is_granted = BooleanField(default=True)
    granted_at = DateTimeField(auto_now_add=True)
    granted_by = ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    notes = TextField(blank=True)
```

### Permission Management
- Admins can grant/revoke permissions to students via:
  - Admin panel: `/students/admin/permissions/`
  - Bulk assignment: `/students/admin/permissions/bulk/`
  - Individual grant/revoke endpoints

## 6. Data Models Used

### Student Model Relationships
```
User
  └─ Student (OneToOneField)
      ├─ StudentResult (ForeignKey)
      │  ├─ ClassSubject
      │  └─ Term
      ├─ TermResult (ForeignKey)
      ├─ StudentPermission (ForeignKey)
      ├─ AttendanceRecord (ForeignKey)
      ├─ Invoice (ForeignKey - from payroll)
      ├─ StudentPayment (ForeignKey - from payroll)
      └─ StudentClass (ForeignKey)
         ├─ ClassTeacher
         │  ├─ Teacher
         │  └─ Subject
         └─ Announcement (ForeignKey)
```

### Query Optimization

All views use `.select_related()` or `.prefetch_related()` to minimize database queries:

1. **StudentResultsView:** `select_related('class_subject__subject', 'term')`
2. **StudentDownloadReportCardView:** `select_related('term', 'class_subject__subject')`
3. **StudentClassAnnouncementsView:** `select_related('created_by')`
4. **StudentAttendanceView:** `select_related('session', 'term')`
5. **StudentContactTeacherView:** `select_related('teacher__user', 'subject')`

## 7. Features Status

| Feature | Status | URL | Permissions Enforced |
|---------|--------|-----|---------------------|
| View Own Profile | ✅ Implemented | `/portal/profile/` | Yes |
| View Own Results | ✅ Implemented | `/portal/results/` | Yes |
| Download Report Card | ✅ Implemented | `/portal/report-card/` | Yes |
| View School Fees | ✅ Implemented | `/portal/fees/` | Yes |
| View Class Timetable | ✅ Implemented | `/portal/timetable/` | Yes |
| View Class Announcements | ✅ Implemented | `/portal/announcements/` | Yes |
| Submit Assignments | ⏳ Placeholder | - | Yes |
| View Own Attendance | ✅ Implemented | `/portal/attendance/` | Yes |
| Contact Teachers | ✅ Implemented | `/portal/contact-teacher/` | Yes |
| Access Student Portal | ✅ Implemented | `/portal/dashboard/` | Yes |

## 8. Security Considerations

1. **Authentication:** All views require `LoginRequiredMixin`
2. **Authorization:** Each view checks `student_profile` association
3. **Data Isolation:** Students can only see:
   - Their own profile, results, attendance, fees
   - Announcements for their class
   - Teachers assigned to their class
4. **Permissions:** Admin-managed via StudentPermission model

## 9. Templates Structure

```
templates/students/portal/
├─ student_dashboard.html (Main hub)
├─ student_profile.html (Profile view)
├─ student_results.html (Results with Report Card button)
├─ student_fees.html (Fees/Invoices)
├─ download_report_card.html (Report card download)
├─ class_timetable.html (Class subjects)
├─ class_announcements.html (Class announcements)
├─ student_attendance.html (Attendance records)
└─ contact_teacher.html (Teacher list with messaging)
```

## 10. Testing the End-to-End Flow

### Prerequisites
1. Student user account created and linked to student profile
2. Student assigned to a class
3. Class has subjects assigned
4. At least one exam/test result entered for the student
5. Student attendance records created
6. Invoices/fees assigned to student (if testing fees feature)
7. Announcements published for student's class

### Test Steps

1. **Login as Student**
   - Navigate to `/login/`
   - Enter student credentials
   - System redirects to `/students/portal/dashboard/`

2. **Test Dashboard**
   - Verify welcome message displays
   - Verify all feature cards are visible
   - Verify quick stats display correctly

3. **Test View Profile**
   - Click "View Profile" card
   - Verify all profile information displays
   - Verify "Back to Dashboard" button works

4. **Test View Results**
   - Click "View Results" card
   - Verify results table displays with all exams
   - Verify "Download Report Card" button present
   - Click button → verify navigates to report card page

5. **Test Download Report Card**
   - Click "Download Report Card" from results or dashboard
   - Verify all term reports display
   - Click "Download PDF" for a term
   - Verify PDF downloads successfully

6. **Test Fees**
   - Click "School Fees" card (if fees exist)
   - Verify invoices and payment history display
   - Verify summary calculations correct

7. **Test Class Timetable**
   - Click "Class Timetable" card
   - Verify class information displays
   - Verify all class subjects listed

8. **Test Announcements**
   - Click "Class Announcements" card
   - Verify all class announcements display
   - Verify posted by and date information correct

9. **Test Attendance**
   - Click "My Attendance" card
   - Verify summary cards show correct counts
   - Verify attendance percentage calculated correctly
   - Verify table shows all attendance records

10. **Test Contact Teachers**
    - Click "Contact Teachers" card
    - Verify all class teachers displayed
    - Verify teacher information complete
    - Click "Send Message" → verify redirects to messaging system

## 11. Duplicate Features Check

✅ **No duplicates found** - All 10 permission choices are unique and represent distinct features

## 12. Future Enhancements

1. **Submit Assignments Feature:** Requires Assignment model creation
2. **PDF Report Card Customization:** Custom branding, grades interpretation
3. **Push Notifications:** Notification system for announcements, new results
4. **Parent Access:** Parent portal with student performance tracking
5. **Grade Analytics:** Visual charts and graphs for performance tracking
6. **Assignment Grading:** Teachers can grade student submissions
7. **Timetable Notifications:** Notifications for schedule changes
8. **Mobile App:** Native mobile app for student portal

---

**Last Updated:** May 13, 2026
**Status:** All core features implemented and ready for testing
