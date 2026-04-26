# Professional Report Card System Guide

## Overview
The Daarul Portal now includes a comprehensive professional report card system with:
- ✅ Printable individual student report cards (Portrait mode)
- ✅ Class broadsheet for teacher review (Landscape mode)
- ✅ Automatic score calculations (test, exam, total, percentage, grade)
- ✅ Conduct/behavior assessment (5 dimensions)
- ✅ Remarks and grade points based on configurable grading scale
- ✅ Print-friendly layouts optimized for A4 paper

---

## Features

### 1. Individual Report Card (Portrait Mode)
**What it shows:**
- School header and student information
- Academic performance table with:
  - Test Score (max: configurable in template)
  - Exam Score (max: configurable in template)
  - Total Score (auto-calculated)
  - Percentage (auto-calculated)
  - Grade (A/B/C/D based on grading scale)
  - Remark (from GradeScale configuration)
  - Subject Position (rank within class for that subject)
- Summary statistics:
  - Total Score for all subjects
  - Average Score
  - Overall Grade
  - Class Position (student's rank in class)
- Conduct & Behavior Assessment:
  - Attendance rating
  - General Conduct
  - Punctuality
  - Attentiveness in class
  - Class Participation
  - Teacher's Comments
- Grade Scale Legend
- Official signature and date fields
- Print timestamp

**How to Print:**
1. Navigate to Results → Student Report Card
2. Select the student and term
3. Click "🖨️ Print Report Card" button
4. Press Ctrl+P or use browser print dialog
5. Set paper size to A4 Portrait
6. Adjust margins if needed
7. Print!

### 2. Class Broadsheet (Landscape Mode)
**What it shows:**
- All students in the class with their scores
- Subject-by-subject performance
- Summary statistics (total, average, position)
- Grade color-coding (green for A, blue for B, yellow for C, red for D)
- Class statistics (total students, total subjects)

**How to Print:**
1. Navigate to Results → Broadsheet
2. Select class and term
3. Click "🖨️ Print Broadsheet" button
4. Set paper size to A4 Landscape
5. Print!

---

## Data Entry Workflow

### Step 1: Create Result Template
1. Admin → Result Templates
2. Create template with:
   - School Class
   - Term
   - Grading Scale (defines A/B/C/D ranges and remarks)
   - Test max score (e.g., 40)
   - Exam max score (e.g., 60)
   - Options for positions, percentages, etc.

### Step 2: Bulk Enter Scores
1. Results → Bulk Entry for Class
2. Select class and term
3. Enter test and exam scores for each student-subject combination
4. **Tab Navigation:** Use Tab key to move between cells
5. **Arrow Keys:** Use arrow keys to move between rows/columns
6. Save all scores at once

### Step 3: Enter Conduct Records
1. Same bulk entry form, different tab: "⭐ Conduct & Behavior"
2. Select ratings for each student:
   - Attendance (Excellent/Very Good/Good/Fair/Poor)
   - Conduct (Excellent/Very Good/Good/Fair/Poor)
   - Punctuality (Always on time/Usually on time/Mostly on time/Often late/Frequently late)
   - Attentiveness (Excellent/Very Good/Good/Fair/Poor)
   - Participation (Excellent/Very Good/Good/Fair/Poor)
3. Add teacher notes/comments
4. Save

### Step 4: Generate Reports
1. For individual student: Results → Student Report Card
2. For class: Results → Class Broadsheet
3. Print or save as PDF

---

## Grading Configuration

### Default Grade Scale:
- **A:** 80-100% (Excellent)
- **B:** 70-79% (Good)
- **C:** 60-69% (Fair)
- **D:** 50-59% (Poor)
- **F:** Below 50% (Fail)

### Customizing:
1. Admin → Grade Scale Management
2. Create/edit scale with:
   - Name (e.g., "NECO 2025")
   - Grade letter (A, B, C, etc.)
   - Min and Max percentage scores
   - Remark (e.g., "Excellent", "Satisfactory")
   - Grade Point (for GPA calculation)

---

## Score Calculation

### Total Score Calculation:
```
Total = (Test Score × Test Weight) + (Exam Score × Exam Weight)

Where:
- Test Weight = Test Max Score / (Test Max + Exam Max)
- Exam Weight = Exam Max Score / (Test Max + Exam Max)
```

Example (Test max=40, Exam max=60):
- Test Weight = 40/100 = 0.4
- Exam Weight = 60/100 = 0.6
- If Student gets Test=35, Exam=55
- Total = (35 × 0.4) + (55 × 0.6) = 14 + 33 = 47/100

### Percentage:
```
Percentage = (Total Score / (Test Max + Exam Max)) × 100
```

### Average (Class-wide):
```
Average = Sum of all subject totals / Number of subjects
```

---

## Print Settings Recommendations

### For Individual Report Cards:
- **Paper Size:** A4
- **Orientation:** Portrait
- **Margins:** 0.5 cm (minimal)
- **Color:** Enable for better presentation
- **Scaling:** 100% (no scaling)
- **Background Graphics:** Enable (for colored grade cells)

### For Broadsheet:
- **Paper Size:** A4
- **Orientation:** Landscape
- **Margins:** 0.5 cm
- **Scaling:** Fit to page (or 90-100%)
- **Background Graphics:** Enable

---

## Troubleshooting

### Issue: Scores not showing on report card
**Solution:** 
- Check that result template is marked as active
- Verify scores were saved (check database)
- Ensure term is active

### Issue: Percentage/Grade showing as empty
**Solution:**
- Both test and exam scores must be entered
- Check GradeScale is configured correctly
- Verify percentage falls within a GradeScale range

### Issue: Conduct fields not showing
**Solution:**
- Enter conduct data from the "Conduct & Behavior" tab in bulk entry
- Ensure student conduct record was created

### Issue: Print layout broken
**Solution:**
- Clear browser cache (Ctrl+Shift+Delete)
- Try different browser
- Check page margins are not set too large
- Disable browser extensions that might interfere

---

## Database Models Overview

### StudentResult
Stores individual subject scores:
- student (FK)
- class_subject (FK)
- term (FK)
- result_template (FK)
- test_score
- exam_score
- total_score (auto-calculated)
- percentage (auto-calculated)
- grade (auto-calculated)
- remark (auto-calculated)
- grade_point (auto-calculated)
- class_position (class rank for subject)
- subject_position (rank among subjects)

### StudentConduct
Stores behavioral/conduct data:
- student (FK)
- term (FK)
- attendance (choices: Excellent, Very Good, Good, Fair, Poor)
- conduct (choices: Excellent, Very Good, Good, Fair, Poor)
- punctuality (choices: Always on time, Usually on time, etc.)
- attentiveness (choices: Excellent, Very Good, Good, Fair, Poor)
- participation (choices: Excellent, Very Good, Good, Fair, Poor)
- teacher_notes (text field)

### TermResult
Summary of all results for a student in a term:
- student (FK)
- term (FK)
- result_template (FK)
- total_score (sum of all subjects)
- average_score (average across subjects)
- grade (overall grade)
- position (rank in class)
- is_complete (flag)

### GradeScale
Defines grading rules:
- name (e.g., "Primary School Scale")
- min_score (percentage)
- max_score (percentage)
- grade (letter: A, B, C, etc.)
- remark (text: "Excellent", etc.)
- grade_point (for GPA)

### ResultTemplate
Configuration for a class/term:
- school_class (FK)
- term (FK)
- grade_scale (FK)
- test_max_score (max test score)
- exam_max_score (max exam score)
- calculate_class_position (bool)
- calculate_subject_position (bool)
- show_percentage (bool)
- show_grade_points (bool)
- show_remarks (bool)
- is_active (bool)

---

## API/Admin Actions

### Creating Grades Programmatically
```python
from results.models import GradeScale, ResultTemplate
from exams.models import Term
from school_classes.models import SchoolClasses

# Create grade scale
scale = GradeScale.objects.create(
    name='Primary 2025',
    min_score=80,
    max_score=100,
    grade='A',
    remark='Excellent',
    grade_point=5.0
)

# Create result template
template = ResultTemplate.objects.create(
    name='Primary 1 - Term 2',
    school_class=SchoolClasses.objects.first(),
    term=Term.objects.get(name='Term 2'),
    grade_scale=scale,
    test_max_score=40,
    exam_max_score=60,
    is_active=True
)
```

---

## Tips & Best Practices

1. **Always configure GradeScale first** - Before entering results
2. **Use Result Templates** - Don't hardcode values
3. **Enter both test AND exam scores** - Total/grade won't calculate with just one
4. **Validate data before printing** - Review on screen first
5. **Use PDF printer** - For archival; go to File > Print > Save as PDF
6. **Batch entry** - Enter all class results at once using bulk entry
7. **Weekly backups** - Database backups important for records
8. **Keep records** - Store printed PDFs for records retention

---

## Support

For issues or questions:
1. Check this guide's Troubleshooting section
2. Review the template files in `templates/results/`
3. Check the Models documentation in the code
4. Contact system administrator

---

## Version History

### v2.0 (Current) - Professional Report Card System
- ✅ New printable report card template (portrait)
- ✅ Enhanced broadsheet (landscape)
- ✅ Conduct/behavior assessment fields
- ✅ Auto-calculations (percentage, grade, position)
- ✅ Configurable grading scale
- ✅ Professional styling and layout

### v1.0 - Basic Results System
- Basic score entry
- Simple report display
