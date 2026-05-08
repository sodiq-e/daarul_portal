# Results & Grading Admin Interface - Complete Guide

## Overview

The Results & Grading Admin Interface provides a streamlined, user-friendly way to manage all results-related settings without requiring access to Django Admin. Admins can now:

✅ Manage academic sessions and terms in bulk  
✅ Add subjects quickly (single or bulk)  
✅ Configure grade scales  
✅ Create result templates for all classes at once  
✅ Assign subjects to classes in bulk  
✅ All with a clean, intuitive interface  

## Access

**URL:** `/results-admin/`  
**Permission:** Admin/Superuser only  
**Sidebar Link:** "Results Settings" (visible only to admins)

---

## 1. Academic Sessions & Terms Management

**Location:** `Results Settings` → `Manage Sessions`

### Features

- **Create New Sessions:** Add academic years like 2024/2025, 2025/2026, etc.
- **Auto-create Terms:** Each new session automatically gets 3 terms (First, Second, Third)
- **Keep Multiple Sessions:** All sessions remain accessible; data is never deleted
- **Activate Terms:** Only ONE term per session should be active at a time for data entry
- **Historical Access:** Old sessions stay in the system for record-keeping

### Workflow

1. At the beginning of the school year, create a new academic session (e.g., 2024/2025)
2. System auto-creates 3 terms for that session
3. Activate the first term when ready to start entering results
4. When moving to the next term, activate it (previous data remains accessible)
5. Next year, create a new session - old data is preserved

### Example

```
Academic Year: 2024/2025
├── First Term (Inactive)
├── Second Term (Inactive)
└── Third Term (Inactive)

Academic Year: 2023/2024
├── First Term (Inactive)
├── Second Term (Inactive)
└── Third Term (Inactive) [Can still view old results]
```

---

## 2. Subjects Management

**Location:** `Results Settings` → `Manage Subjects`

### Features

- **Add Single Subject:** One subject at a time
- **Bulk Add:** Add multiple subjects at once using formatted text
- **Subject Codes:** Optional code for shorthand reference (e.g., ENG, MATH, SCI)
- **Toggle Status:** Activate/deactivate subjects as needed

### Bulk Format

Paste subjects in this format (one per line):
```
English Language
Mathematics
Science | SCI
Social Studies | SOC
Physical Education | PE
```

After the pipe (|), the code is optional.

### Usage

1. Go to "Manage Subjects"
2. Either:
   - Fill "Add Single Subject" form, OR
   - Paste multiple subjects in "Bulk Add" textarea
3. Review subjects in the table below
4. Deactivate subjects if they're no longer taught

---

## 3. Grade Scales Configuration

**Location:** `Results Settings` → `Manage Grades`

### Features

- **Multiple Scales:** Create different grading systems (Standard, WAEC, Cambridge, etc.)
- **Score Ranges:** Define min/max scores for each grade
- **Remarks:** Add remarks (Excellent, Very Good, Good, etc.)
- **Grade Points:** For GPA calculation

### Example Grade Scale

```
Standard Scale:
├── A: 80-100 (Excellent) [GP: 4.0]
├── B: 70-79 (Very Good) [GP: 3.5]
├── C: 60-69 (Good) [GP: 3.0]
├── D: 50-59 (Fair) [GP: 2.0]
├── E: 40-49 (Pass) [GP: 1.0]
└── F: 0-39 (Fail) [GP: 0.0]
```

### Add New Grade

1. Enter scale name (e.g., "Standard", "WAEC")
2. Enter score range (min-max)
3. Enter grade letter
4. Enter remark
5. (Optional) Enter grade point for GPA

---

## 4. Result Templates

**Location:** `Results Settings` → `Manage Templates`

### Features

- **Bulk Create:** Create templates for multiple classes at once
- **Configure Scores:** Set test/exam max scores (default: 40/60)
- **Assign Grade Scales:** Choose grading system for each template
- **Activate/Deactivate:** Enable templates for result entry

### Workflow

1. Select the term
2. Choose multiple classes (Ctrl+Click to select)
3. Choose grade scale
4. Set test/exam max scores
5. Click "Create Templates"

### What Happens

- Templates are created for each selected class in the chosen term
- Templates start as inactive
- Activate templates before teachers enter results

---

## 5. Class-Subject Assignments

**Location:** `Results Settings` → `Assign Subjects`

### Features

- **Assign to One Class:** Select a class
- **Assign Multiple Subjects:** Use Ctrl+Click to select multiple subjects
- **Bulk Assignment:** All selected subjects are assigned at once
- **Remove Assignments:** Delete subject-class links as needed

### Workflow

1. Select a class from the dropdown
2. Hold Ctrl (Cmd on Mac) and click subjects to select multiple
3. Click "Assign Subjects"
4. Review assignments in the table

### Note

- Each class can have multiple subjects
- Each subject can be assigned to multiple classes
- Display order is set automatically during assignment

---

## Complete Setup Workflow

Follow this sequence for initial setup:

### Step 1: Create Academic Session
```
Results Settings → Academic Sessions
→ Enter "2024/2025" → Create Session
✓ Creates First, Second, Third Term
```

### Step 2: Add Subjects
```
Results Settings → Manage Subjects
→ Bulk paste all subjects
→ Subjects are now available system-wide
```

### Step 3: Configure Grades
```
Results Settings → Manage Grades
→ Add grades for each scale
→ Example: A (80-100), B (70-79), etc.
```

### Step 4: Assign Subjects to Classes
```
Results Settings → Assign Subjects
→ Select Class 1
→ Select all subjects for that class
→ Repeat for each class
```

### Step 5: Create Result Templates
```
Results Settings → Manage Templates
→ Select Term: First Term 2024/2025
→ Select all classes
→ Select grade scale
→ Create templates
```

### Step 6: Activate Term
```
Results Settings → Academic Sessions
→ Activate "First Term 2024/2025"
✓ Teachers can now enter results
```

---

## Tips & Best Practices

### 🎯 Session Management
- Create sessions at the beginning of each academic year
- Keep old sessions for historical data access
- Only activate the current term
- Never delete old data

### 📚 Subject Management
- Use meaningful subject names
- Add codes for easier reference
- Deactivate subjects no longer taught
- Once assigned to a class, you can still toggle status

### ⭐ Grade Scales
- Create one scale that all classes use, OR
- Create multiple scales if departments use different systems
- Ensure grade ranges don't overlap
- Test different grade ranges before finalizing

### 📋 Result Templates
- Create templates BEFORE teachers start entering results
- Ensure all classes have templates for active terms
- Test with one class first
- Activate templates only when ready for data entry

### 🔗 Class-Subject Links
- Assign all required subjects to each class BEFORE creating templates
- Review assignments to ensure no subjects are missing
- Remove subjects that are no longer taught
- Can adjust subjects even after templates are created

---

## Troubleshooting

### Problem: Can't see classes in template creation
**Solution:** Ensure classes exist in the system and have students enrolled.

### Problem: Grade scale not available
**Solution:** Go to "Manage Grades" and ensure at least one grade scale exists for the system.

### Problem: Teachers can't enter results
**Solution:** 
1. Check that result templates are created for the class-term
2. Check that the template is marked as active
3. Verify the term is activated in Academic Sessions

### Problem: Can't remove a subject from a class
**Solution:** Use the remove button in the Class-Subject Assignment view.

---

## Fallback: Django Admin Access

If you need advanced features or direct database access:
- Click "Django Admin" on the Results Settings dashboard
- Or navigate to `/admin/`
- Access settings from there

---

## Support

For questions or issues with the Results Settings interface, contact the system administrator.
