# 10. Attendance Module

## Feature Overview
The attendance module handles recording student attendance, managing holiday and term restrictions, and supporting teacher-based attendance entry.

## Core Features

### Attendance Record Management
- Entry point: /attendance/
- Views: AttendanceRecordListView, AttendanceRecordDetailView, AttendanceRecordCreateView, AttendanceRecordUpdateView, AttendanceRecordDeleteView
- Models: AttendanceRecord, AttendanceSession, AttendanceHoliday, AttendanceSettings
- Templates: templates/attendance/attendance_list.html and related templates

Workflow:
1. Staff/teacher opens attendance records
2. Records are filtered by class/date/term
3. Attendance entries are created or modified
4. The system stores the status for each student and date

### Teacher Attendance Marking
- Entry point: teacher attendance view
- View: TeacherAttendanceMarkView
- Template: templates/teachers/attendance/mark_attendance.html
- Permission: requires the mark_attendance permission

Workflow:
1. Teacher chooses a class and date
2. The system checks for holidays and term-date restrictions
3. Student attendance records are loaded
4. Teacher submits the attendance data

### Holiday/Term Rules
- The view uses AttendanceHoliday and Term date ranges to enforce business rules
- If no current term is configured, the system can block attendance entry outside configured boundaries

## Data Model Notes
- AttendanceRecord is linked to student/class/date
- AttendanceSession stores session-level day type data
- AttendanceHoliday stores school holiday ranges
- AttendanceSettings stores app-wide attendance settings

## Validation Rules
- Attendance can be blocked for non-school days or out-of-term dates
- There are explicit checks for holiday dates and configured academic terms

## Permission Checks
- Teacher can only mark attendance if they have the relevant permission
- Class assignments determine which classes a teacher can mark for

## Dependencies
- Depends on students, school_classes, and exams.Term
