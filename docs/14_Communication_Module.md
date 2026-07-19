# 14. Communication Module

## Feature Overview
The communication module handles public contact messages, admin replies, and portal-based messaging between administrators and registered users.

## Core Features

### Public Contact Form
- Entry point: /contact/ (via communication URLs)
- View: contact_view
- Template: templates/contact.html
- Model: Message

Workflow:
1. Visitor submits a name, email, subject, and message
2. The message is stored in the database
3. A contact notification email is sent to the school
4. A confirmation email is sent to the sender if an email address exists
5. The user is redirected to a success page

### Admin Message Management
- Entry points: admin message list/detail views
- Views: AdminMessageListView, AdminMessageDetailView
- Templates: templates/communication/admin_messages_list.html and related templates

Workflow:
1. Admin opens the list of inbound messages
2. Admin can read and reply to a message
3. Reply can be stored as a portal message or sent by email

### Portal Messaging
- Entry points: portal inbox and thread views
- Views: AdminPortalUserListView, AdminPortalThreadView, PortalInboxView, PortalThreadDetailView
- Models: PortalThread, PortalMessage

Workflow:
1. Admin or user opens a portal thread
2. Messages are exchanged through thread records
3. Unread counts and latest message metadata are computed

## Validation Rules
- Reply text cannot be empty for admin replies
- Bulk portal messages require selected users and content

## Permission Checks
- Admin message management requires admin-level permissions
- Portal inbox is available to authenticated users who have a portal thread

## Dependencies
- Relies on settingsapp.email_service for sending contact emails
