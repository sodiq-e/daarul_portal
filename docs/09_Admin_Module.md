# 09. Admin Module

## Feature Overview
The admin module is the control center for school-wide management. It uses Django admin plus custom admin workflows for approvals, publication, settings, and moderation.

## Django Admin Integration
- Standard Django admin site is mounted at /admin/
- The project also registers many models through app admin.py modules

## Admin Capabilities

### User Approval and Role Management
- Profile approval controls user account activation and group assignment
- Admins can review and approve student registrations and teacher profiles

### Student Application Review
- Admins review applications from the student application list view
- They can accept or reject pending entries

### Exam Paper Approval
- Admins review exam papers and approve or reject them
- Approval logs record each decision

### Results Publication
- Results can be published or unpublished through results-admin routes
- Publication controls visibility to students and portal users

### School Settings Management
- Admins can update school-wide settings, gallery images, and school branding

### Communication Moderation
- Admins can view incoming contact messages and reply via email or portal message
- Bulk portal messaging is available to active users

## Entry Points
- /admin/
- /results-admin/
- /settings/
- /students/applications/
- /exams/teacher/approval/ or related review routes

## Core Permissions
- Admin access typically relies on user.is_staff and approved profile state
- Some admin views are not purely Django admin but custom views with explicit checks

## Business Logic
- Approvals update the appropriate model state and often record who performed the approval
- Publication flows change is_published flags and related timestamps
- Settings changes affect the entire school site
