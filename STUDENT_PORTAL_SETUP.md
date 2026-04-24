# Student Portal Setup Guide

## Overview
Students can now log in to the portal to view their personal information, academic results, and school fee records.

## How It Works

1. **Student Creates Account**: A student creates a login account and requests the "Student" role during signup
2. **Admin Approves**: An administrator approves the student account
3. **Admin Links Student**: Staff links the student user account to the corresponding Student record in the system
4. **Student Access**: Once linked, the student can log in and access:
   - Personal profile information
   - Academic results and grades
   - School fees, invoices, and payment history

## Setup Instructions for Staff

### Step 1: Student Registration
- Student visits the portal and creates an account
- During registration, they select "Student" as their role
- Account waits for approval

### Step 2: Account Approval
- Admin goes to the admin panel (`/admin/`)
- Navigates to "Accounts" → "Profiles"
- Finds the pending student account and marks it as "is_approved"
- This activates the student's login

### Step 3: Link Student Account (Important!)
Once the student account is approved:

1. Go to `/admin/students/student/`
2. Find the student record in the list
   - Look for students marked with "✗ Not linked" in the "User Account" column
3. Click to edit the student
4. In the "Student Login Account" section, use the **User** dropdown to select the corresponding user account
5. Save

**Important**: Make sure you match the correct student with the correct user account!

## Student Portal Access

### URL: `/students/portal/dashboard/`
Students can access their portal from the home page after logging in.

### Available Features

#### 1. Dashboard (`/students/portal/dashboard/`)
- Quick summary of student information
- Current class and status
- Number of pending invoices
- Total amount owing

#### 2. Profile (`/students/portal/profile/`)
- Full personal information
- Admission number
- Date of birth
- Current class assignment
- Student status

#### 3. Results (`/students/portal/results/`)
- View all academic results by subject
- See exam names and dates
- Check grades for each subject

#### 4. School Fees (`/students/portal/fees/`)
- Summary of total due, paid, and owing
- List of all invoices with status
- Payment history
- Invoice status: Pending, Paid, or Overdue

## Security Notes

- Each student can only see their own information
- The system prevents students from viewing other students' data
- Account linking ensures data privacy and prevents unauthorized access
- Students must be "approved" before they can log in

## Troubleshooting

### Student Can't See Their Portal Menu
**Cause**: Student account not linked to Student record
**Solution**: Follow Step 3 above to link the account

### "No student profile linked to your account" Error
**Cause**: User account exists but has no linked Student record
**Solution**: Go to `/admin/students/student/` and link the user to a Student

### Missing Results or Fees Data
**Cause**: Data hasn't been created in the system yet
**Solution**: Admin needs to create the student's results and fee invoices through the admin panel

## Admin Tips

- Filter students by "User Account" status to quickly see which students are linked
- Use the search box to find students by admission number, name, or username
- The student list now shows a checkmark (✓) if linked, or X (✗) if not linked
- When editing a student, you can see the linked user's full details in the readonly "Account Details" field
