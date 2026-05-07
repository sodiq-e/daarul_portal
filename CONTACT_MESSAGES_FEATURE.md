# Contact Messages Management System

## Overview
This feature allows administrators to manage contact form messages submitted through the contact page. Admins can view all messages and send replies directly to the senders via email or through the portal system.

## What Was Added

### 1. **Database Changes**
- Updated `Message` model in `communication/models.py` with new fields:
  - `user` (ForeignKey to User) - Links message to a user account if they have one
  - `is_replied` (Boolean) - Tracks if admin has replied
  - `reply_message` (TextField) - Stores the admin's reply text
  - `replied_at` (DateTime) - Timestamp of when reply was sent
  - `replied_by` (ForeignKey to User) - Which admin sent the reply
  - `reply_method` (CharField) - Either 'email' or 'portal'

### 2. **New Admin Views**
Created two new class-based views for admin message management:

#### `AdminMessageListView`
- Lists all contact messages with pagination (20 per page)
- Shows count of replied and unreplied messages
- URL: `/contact/admin/messages/`
- Access: Admin users only (staff with approved profile)

#### `AdminMessageDetailView`
- Displays full message details
- Shows sender information (name, email, phone, user account status)
- Allows admin to write and send a reply
- Handles both account holders and non-account holders
- URL: `/contact/admin/messages/<int:pk>/`
- Access: Admin users only

### 3. **New Templates**

#### `communication/templates/communication/admin_messages_list.html`
- Clean admin interface to list all messages
- Shows unreplied vs replied message counts
- Quick status indicators
- Links to view individual messages

#### `communication/templates/communication/admin_message_detail.html`
- Full message display
- Reply form (textarea for admin response)
- Shows whether sender has account
- Displays existing reply if message already replied to

### 4. **New URLs**
Added to `communication/urls.py`:
- `/contact/admin/messages/` - List all messages
- `/contact/admin/messages/<id>/` - View and reply to specific message

### 5. **Database Migration**
- Migration file: `communication/migrations/0002_alter_message_options_message_is_replied_and_more.py`
- Already applied to local database

### 6. **Admin Sidebar Link**
- Added "Contact Messages" link in admin menu (base.html)
- Only visible to staff users
- Icon: 📧

## How to Use

### For Admin Users:

1. **Access Messages Page**
   - Log in as admin
   - Go to sidebar → "Contact Messages" OR
   - Navigate to: `/contact/admin/messages/`

2. **View All Messages**
   - See list of all contact submissions
   - Green badge = Already replied
   - Red badge = Pending reply
   - Click "View Details" to open message

3. **Reply to a Message**
   - Click message from list
   - Read sender's information and message
   - Type your reply in the text box
   - Click "Send Reply"
   
4. **Auto-Send Logic**
   - **If sender has account**: Reply sent via email + Portal message notification
   - **If no account**: Reply sent via email only

## Technical Details

### Reply Flow:
```
Contact Form Submission → Message Saved → Admin Notification Email
                                          ↓
                          Admin views message in portal
                                          ↓
                          Admin writes & submits reply
                                          ↓
                    (Has Account?)  ←-----+-----→  (No Account?)
                          ↓                              ↓
                    Email Sent                    Email Sent
                    Portal Message Created
```

### Email Configuration:
- Uses existing `settingsapp.email_service`
- Sender email: `settings.DEFAULT_FROM_EMAIL`
- Subject: "Reply to Your Message - [SCHOOL_NAME]"
- Uses plain text emails (can be enhanced with HTML templates)

## Important Notes

### ✅ What Wasn't Changed:
- Contact form (`contact_view`) works exactly as before
- Existing contact messages are preserved
- No breaking changes to URLs or models' original fields
- All original contact functionality intact

### 📋 Deployment to PythonAnywhere:

1. **Push Changes to Git**
   ```bash
   git add .
   git commit -m "Add contact message management system"
   git push origin main
   ```

2. **Pull on PythonAnywhere**
   ```bash
   cd /home/[username]/daarul_portal
   git pull origin main
   ```

3. **Run Migration**
   ```bash
   python manage.py migrate communication
   ```

4. **Reload App**
   - Go to PythonAnywhere Web tab → Reload app

5. **Done!**
   - Admin message management now live on production

## Admin Interface Features

### List View:
- Pagination (20 messages per page)
- Filter by replied status
- Search messages by sender name/email
- Shows message preview
- Quick status indicators

### Detail View:
- Full message text
- Sender contact info
- Account status indicator
- Reply history (if already replied)
- Beautiful responsive design

## Additional Admin Features

### Django Admin Panel:
- Access via `/admin/communication/message/`
- All new fields visible and editable
- Can mark messages as replied manually if needed
- Filter by is_replied, created date, reply method

### Display in Admin List:
- Name, Email, Created Date, Replied Status, Reply Method
- Color-coded filters for quick access

## Security & Permissions:
- Only staff/admin users can access message management
- Permission checks via `is_admin()` function
- Profile must be approved (is_approved=True)
- CSRF protection on reply forms

## Future Enhancements (Optional):
- HTML email templates
- Multiple admin replies/conversation
- Message categories/tags
- Reply templates
- SMS reply option
- Attachment support
- Message categories

## Troubleshooting

### Migrations Issue:
If migration fails, run:
```bash
python manage.py migrate --run-syncdb
```

### Email Not Sending:
Check:
1. `settings.DEFAULT_FROM_EMAIL` is set
2. Email backend configured in `.env`
3. Check Django admin console for errors
4. Test with: `python manage.py shell`

### Can't Access Admin Messages:
- Ensure user has `is_staff=True`
- Check user profile has `is_approved=True`
- Verify user is in appropriate group (Teacher/Staff)

## Files Modified/Created:
✓ `communication/models.py` - Updated Message model
✓ `communication/views.py` - Added new views
✓ `communication/urls.py` - Added new routes
✓ `communication/admin.py` - Enhanced admin interface
✓ `communication/templates/communication/admin_messages_list.html` - New template
✓ `communication/templates/communication/admin_message_detail.html` - New template
✓ `communication/migrations/0002_...py` - Database migration
✓ `templates/base.html` - Added sidebar link

## Questions or Issues?
If you encounter any problems:
1. Check Django console for error messages
2. Run `python manage.py check`
3. Verify all migrations are applied: `python manage.py migrate --list`
4. Clear browser cache and try again
