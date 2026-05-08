# Guardian Information Fix - Implementation Guide

## Problem
Student details page was not showing parent/guardian contact information.

## Root Cause
Existing students in the database were created before the guardian information transfer feature was implemented. New students will get guardian info automatically, but existing ones need to be backfilled.

## Solution Implemented

### 1. **Django Signal Updated** (`students/signals.py`)
   - When a student application is approved, the signal now automatically copies all guardian fields from the application to the new Student record.
   - Fields transferred:
     - `guardian_name`, `guardian_relationship`, `guardian_phone`, `guardian_email`
     - `guardian_address`, `guardian_occupation`, `guardian_employer`
     - `emergency_contact_name`, `emergency_contact_phone`

### 2. **Management Command Created** (`students/management/commands/backfill_guardian_info.py`)
   - Updates all existing student records with guardian info from their approved applications

### 3. **Student Detail Template Updated** (`templates/students/student_detail.html`)
   - Guardian information only displays for class teachers (security feature)
   - Shows parent contact info with clickable phone/email links

## How to Use

### Step 1: Run the Backfill Command
On your server (PythonAnywhere or local), run:

```bash
python manage.py backfill_guardian_info
```

This will:
- ✓ Find all approved student applications
- ✓ Match them with student records
- ✓ Copy guardian information to students
- ✓ Show a summary of updates

### Optional: Force Update Existing Data
If you want to update students who already have guardian info:

```bash
python manage.py backfill_guardian_info --force
```

## What Happens After

✅ **Existing Students:** Guardian info will be populated from their applications  
✅ **New Applications:** When approved, guardian info automatically transfers via the signal  
✅ **Class Teachers:** Can now see parent contact details in the student profile  
✅ **Security:** Only class teachers see this sensitive information

## Verification

1. Go to any student's detail page
2. If you're a class teacher for that student's class, you'll see a "Guardian Information" section with:
   - Parent name
   - Relationship
   - Phone (clickable tel: link)
   - Email (clickable mailto: link)
   - Occupation
   - Employer
   - Emergency contact info

## Files Modified
- `students/signals.py` - Added guardian field transfers
- `students/management/commands/backfill_guardian_info.py` - Backfill command
- `templates/students/student_detail.html` - Template to display guardian info
