# Exam Paper Workflow - Quick Reference Guide

## For Teachers

### Creating an Exam Paper (Step by Step)

**1. Start New Exam**
- Go to Exams → Create Exam Paper
- Select: Subject, Class, Term, Academic Year
- Enter: Duration and Instructions (with rich editor)
- Enable **Include marks and correct-answer fields** at the top of the settings only if this paper uses scoring; this reveals total, section, and question marks plus the correct-answer inputs.
- When disabled, the fields are hidden and marks are omitted from student-facing preview, printout, and exports; existing values are preserved if the setting is turned off.
- Click Save

**2. Create Sections**
- Click "Add Section"
- Select type: Objective, Theory, etc.
- Add section instruction (optional)
- Set marks allocation for section
- Choose the section font family and size for preview and print
- Save

**3. Add Questions**
- Click "Add Question" in section
- **Write Question Text:**
  - Use CKEditor toolbar to format
  - Add Bold, Italic, Lists as needed
  - **Insert Image:** Click Image icon → Upload → Place in text
  - **Add Diagram:** Set a custom width (40–1200 px), choose inline placement or its own line, then use **Render size** to update the diagram in the editor; a text status confirms the applied size without displaying a second copy. The requested pixel width is saved as a proportional image size for the printed page so the whole drawing scales without cropping. Export includes only the shapes, with a small transparent margin—not the drawing board or grid. Inserted diagrams autosave with the exam. Drawings are committed when the pointer is released, even if it leaves the canvas.
  - **Add Table:** Click Table icon → Customize rows/columns
  - **Add Math:** Type LaTeX notation (e.g., `$x^2 + y^2 = z^2$`)
  
- **Set Question Details:**
  - Mark value (points)
  - Question type (Multiple Choice, Essay, etc.)
  - Difficulty level
  - Topic (for organization)

- **Add Teacher Guide:**
  - Suggested answer
  - Solution steps
  - Teaching notes
  - Images/diagrams of solution

- **Add Student Explanation (optional):**
  - Explanation shown after student answers
  - Can include hints or learning resources

- **Save Question**

**4. Add Answer Choices (if Multiple Choice)**
- Click "Add Choice"
- Enter choice text (or copy from CKEditor with formatting)
- Mark correct choice
- Click Save

**5. Preview Exam**
- Click "Preview Exam" button
- Check:
  - ✓ All text displays correctly
  - ✓ Images appear properly
  - ✓ Tables are formatted
  - ✓ Question marks are correct
  - ✓ No dashboard styling (clean layout)
- Print/Save as PDF to check print layout

### Importing an Exam

- Select a `.docx` or `.json` file in the exam builder and click **Import File**.
- For Word documents, choose either:
  - **Parse into editable questions** to detect numbered questions, section headings, and A–E choices.
  - **Preserve document as one question** to keep the document’s text, basic formatting, tables, and supported embedded images together.
- JSON imports must use the exam editor’s save-payload format, including a `sections` array. Metadata fields such as `subject`, `school_class`, and `term` use the corresponding record IDs:

```json
{
  "subject": 1,
  "school_class": 1,
  "term": 1,
  "academic_session": "2026/2027",
  "duration": "1 hour",
  "total_marks": 100,
  "scoring_enabled": true,
  "instructions": "",
  "sections": [
    {
      "title": "Section A",
      "section_type": "objective",
      "instruction": "",
      "marks_allocation": 10,
      "font_family": "Arial",
      "font_size": "12pt",
      "questions": [
        {
          "question_type": "objective",
          "question_text": "<p>Example question</p>",
          "marks": 1,
          "options": [
            {"option_label": "A", "option_text": "Option one"},
            {"option_label": "B", "option_text": "Option two"}
          ]
        }
      ]
    }
  ]
}
```

- Word imports support `.docx`; legacy `.doc` files are not supported.
- Review imported questions and embedded images before saving. Use the rich-text editor’s image upload to add or adjust question images.
- The preview and print layout use the school portal header and the compact exam-paper layout. Each section’s chosen font family and size are saved with the paper.

**6. Submit for Approval**
- Click "Submit for Approval" button
- Paper moves to "Pending" status
- **You cannot edit while pending**
- Wait for admin feedback
- If rejected/returned, you can edit and resubmit

### Using the CKEditor Toolbar

**Text Formatting:**
- Bold (Ctrl+B)
- Italic (Ctrl+I)
- Underline (Ctrl+U)
- Subscript / Superscript

**Lists:**
- Numbered list
- Bulleted list
- Indent/Outdent for sublists

**Media:**
- Image: Drag-drop or click to upload
- Table: Create rows/columns
- Special characters (Σ, ∑, √, etc.)

**Alignment:**
- Left, Center, Right, Justify

**Styles:**
- Heading levels
- Font size
- Text color
- Background color

**Advanced:**
- Link insertion
- Block quote
- Code formatting
- Full screen editing

## For Admins

### Reviewing Exam Papers

**1. Access Pending Reviews**
- Go to Dashboard → Exams → Pending Approval
- See statistics: Pending, Approved, Rejected counts

**2. Review Paper**
- Click "Review" button
- Scrolls through full exam with:
  - ✓ Question text with media
  - ✓ Teacher guide and solutions
  - ✓ Student explanations
  - ✓ Formatting preview

**3. Make Decision**
- Choose action: Approve / Return / Reject
- Add feedback notes (required for return/reject, recommended for approve)
- Click "Submit Decision"

### Actions Explained

| Action | When to Use | Result |
|--------|------------|--------|
| **Approve** | Paper is ready for use | Status → Approved, ready for export |
| **Return for Review** | Minor fixes needed | Back to draft, teacher edits and resubmits |
| **Reject** | Major issues | Marked rejected, teacher may start over |

### Exporting Exams

**1. Access Approved Exams**
- Go to Dashboard → Exams → Approved Papers

**2. Choose Export Format**

**DOCX (Word):**
- Editable in Microsoft Word
- Can make final adjustments
- Best if printing from office
- Preserves all formatting

**PDF:**
- Print-ready immediately
- Cannot edit
- Clean layout
- Smaller file size

**3. Export Options**
- Include Answers: Yes/No (for teacher copy)
- Include Marks: Yes/No (for student copy)

**4. Download and Print**
- Click format button
- File downloads
- Open in Word or Acrobat
- Print directly

### Approval History

- Track all approvals and rejections
- See timestamps and feedback
- View who approved/rejected
- See approval notes

## Workflow Diagram

```
Teacher                                    Admin
─────────────────────────────────────────────────

Create Exam
  ↓
Add Sections
  ↓
Add Questions w/ Media
  ↓
Add Teacher Guides
  ↓
Preview Exam
  ↓
Submit for Approval  ───────→  Pending Dashboard
                        ├─→ Review (See everything)
                        ├─→ Approve ──→ Approved State
                        ├─→ Return   ──→ Back to Edit
                        └─→ Reject   ──→ Rejected State

(If returned/rejected)
  ↓
Edit & Fix Issues
  ↓
Resubmit
  ↓
                    ─────→ Review Again
                        ├─→ Approve ──→ Ready for Export
```

## Tips & Best Practices

### For Teachers

1. **Before Submitting:**
   - Always preview exam first
   - Check all images load correctly
   - Verify all marks add up
   - Have colleague review if possible

2. **Using Rich Editor:**
   - Keep questions clear and concise
   - Use formatting sparingly (bold for emphasis)
   - Break long questions into numbered parts
   - Use tables for data-heavy questions

3. **Images:**
   - Use high-quality images
   - Not too large (auto-scaled)
   - Save separately before uploading

4. **Feedback:**
   - If rejected, read admin feedback carefully
   - Ask for clarification if unsure
   - Make all recommended changes before resubmit

### For Admins

1. **Quality Checks:**
   - Verify question clarity
   - Check answer key accuracy
   - Ensure marks allocation is fair
   - Check for copyright/plagiarism

2. **Feedback:**
   - Be specific: "Image on Q5 unclear" vs "Fix images"
   - Be encouraging: "Great questions, minor edits needed"
   - Provide actionable feedback

3. **Export Best Practices:**
   - Use DOCX for final adjustments
   - Use PDF for printing/distribution
   - Always include marks for teachers
   - Remove answers for student copies

## Troubleshooting

### Image Not Showing
- Check image is uploaded (may take 2-3 seconds)
- Try refreshing page
- Image size should be under 5MB

### CKEditor Not Loading
- Clear browser cache
- Refresh page (Ctrl+F5)
- Check browser is JavaScript-enabled

### Export Not Working
- Check exam is approved
- Verify no special characters in filename
- Try different format (PDF vs DOCX)

### Changes Not Saving
- Check internet connection
- Ensure not pending approval
- Try saving again after 10 seconds

## Support

- Contact: Admin Dashboard → Help
- Documentation: Exam Workflow Guide (in system)
- Common Issues: See Troubleshooting section above

---

**Last Updated:** June 2026
**Version:** 1.0
