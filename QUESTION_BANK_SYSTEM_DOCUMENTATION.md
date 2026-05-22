# Question Bank & Randomization System Implementation

## Overview

This document describes the comprehensive implementation of the Question Bank System with randomization, question categorization, and a question navigator UI for the CBT (Computer-Based Test) module.

## System Components

### 1. Database Models (cbt/models.py)

#### QuestionBank
- Independent container for reusable questions
- Fields:
  - `name`: Question bank identifier
  - `subject`: Foreign key to Subject
  - `school_class`: Optional class association
  - `term`: Optional term association
  - `description`: Bank description
  - `created_by`: Teacher who created the bank
  - `created_at`, `updated_at`: Timestamps
- Methods:
  - `get_question_count()`: Returns active question count

#### CBTExam (Enhanced)
- Added fields for randomization configuration:
  - `question_mode`: MANUAL or RANDOM selection
  - `question_bank`: Optional link to QuestionBank
  - `randomize_questions`: Boolean for question order randomization
  - `randomize_answers`: Boolean for option order randomization
  - `total_questions_to_display`: Number of questions for random mode
  - `balance_by_difficulty`: Attempt to balance difficulty levels
  - `balance_by_topic`: Attempt to balance topics
  - `allow_navigation`: Allow students to see question grid
  - `one_at_a_time`: Display one question per page
  - `show_instant_results`: Show correctness immediately
  - `show_corrections`: Show explanations after submission
  - `allow_review`: Allow returning to previous answers

#### CBTQuestion (Enhanced)
- Added fields:
  - `question_bank`: Foreign key to QuestionBank (optional)
  - `topic`: Question topic for categorization
  - `difficulty`: easy/medium/hard for balancing
  - `created_at`: Timestamp for sorting
- Questions can now exist independently of exams via question banks

#### StudentAttemptQuestion (New)
- Tracks randomized question order per student attempt
- Fields:
  - `attempt`: Foreign key to CBTStudentAttempt
  - `question`: Foreign key to CBTQuestion
  - `randomized_position`: Question display order (1, 2, 3...)
  - `randomized_choice_order`: JSON array of choice IDs in randomized order
  - `is_answered`: Boolean tracking answer status
  - `is_flagged`: Boolean for flagged for review status
  - `created_at`: Timestamp
- Methods:
  - `get_randomized_choices()`: Returns choices in randomized order

### 2. Randomization Logic (cbt/services.py)

#### Core Functions

##### `generate_attempt_seed(attempt_uuid, salt='')`
- Creates deterministic seed from attempt UUID
- Uses MD5 hash for consistency across sessions
- Returns integer seed for random.seed()

##### `get_questions_for_exam(exam)`
- Returns questions based on exam's question_mode
- For RANDOM mode: uses question_bank questions
- For MANUAL mode: uses exam's direct questions

##### `select_random_questions(questions, total_to_display, seed=None)`
- Selects specified number of questions randomly
- Accepts seed for deterministic selection
- Returns list of question objects

##### `shuffle_choices_for_question(question, seed=None)`
- Randomizes option order for a question
- Returns JSON-serializable list of choice IDs

##### `create_attempt_with_randomization(exam, student=None, session_key=None)`
- Main function to create student attempt
- Creates StudentAttemptQuestion records for each question
- Applies randomization using deterministic seeds
- Preserves randomization across refresh/reconnect

### 3. Admin Interface (cbt/admin.py)

Registered models with enhanced interfaces:
- **QuestionBankAdmin**: Inline question editor, list display with question count
- **CBTExamAdmin**: Organized fieldsets for exam configuration, question selection, randomization, behavior settings
- **CBTQuestionAdmin**: Categorization fields (topic, difficulty) prominently displayed
- **StudentAttemptQuestionAdmin**: Tracks question state (answered, flagged)

### 4. View Layer

#### Question Bank Management Views (cbt/question_bank_views.py)

##### TeacherQuestionBankListView
- Lists all banks created by current teacher
- Search by name/description
- Filter by subject, class
- Paginated display with stats

##### QuestionBankCreateView, UpdateView, DeleteView
- CRUD operations for question banks
- Access control ensures only creator can edit/delete

##### QuestionBankDetailView
- Displays all questions in a bank
- Search questions by text, topic
- Filter by difficulty, type
- Quick access buttons for edit/clone

##### QuestionCreateView, UpdateView, DeleteView
- Create/edit questions within a bank
- Inline choice editor (4 extra blank choices)
- Categorization fields (topic, difficulty)
- Support for short answer, MCQ, true/false

##### QuestionCloneView
- Clone existing question to create variant
- Clones prompt, type, marks, explanation, topic, difficulty
- Also clones all choices

##### QuestionSearchAPIView
- JSON API endpoint for dynamic question search
- Returns: id, prompt (truncated), type, difficulty, topic, mark_value
- Supports search, difficulty/topic/type filters

#### URLs (cbt/teacher_urls.py)

Question bank routes (under `/teacher/cbt/`):
```
question-banks/                          → TeacherQuestionBankListView
question-banks/add/                      → QuestionBankCreateView
question-banks/<id>/                     → QuestionBankDetailView
question-banks/<id>/edit/                → QuestionBankUpdateView
question-banks/<id>/delete/              → QuestionBankDeleteView
question-banks/<id>/questions/add/       → QuestionCreateView
questions/<id>/edit/                     → QuestionUpdateView
questions/<id>/delete/                   → QuestionDeleteView
questions/<id>/clone/                    → QuestionCloneView
api/search-questions/                    → QuestionSearchAPIView
```

### 5. Forms (cbt/forms.py)

#### QuestionBankForm
- name, subject (required), school_class, term, description
- Bootstrap styling for form inputs

#### CBTExamForm (Enhanced)
- Added question_mode, question_bank, randomization fields
- Added exam behavior options (navigation, corrections, etc.)
- Organized fieldsets for better UX
- Bootstrap form styling throughout

#### CBTQuestionForm (Enhanced)
- Added topic, difficulty fields
- Improved styling with form-control classes
- Textarea for prompt and explanation

#### CBTChoiceForm, CBTChoiceFormSet
- Inline formset for managing answer choices
- Delete existing choices
- Add up to 4 new blank choices per form

### 6. Question Navigator UI (static/js/cbt-navigator.js)

#### QuestionNavigator Class
Constructor options:
- `containerId`: ID of container element
- `currentQuestion`: Current question index
- `totalQuestions`: Total questions in exam
- `onQuestionChange`: Callback when question changes
- `questionStates`: Dict of question states (answered/unanswered/flagged)
- `allowNavigation`: Enable question grid
- `oneAtATime`: One question per page mode

Methods:
- `render()`: Render navigator UI
- `goToQuestion(num)`: Navigate to specific question
- `updateQuestionState(num, state)`: Update question state
- `markCurrentAnswered()`: Mark current as answered
- `markCurrentFlagged()`: Mark current as flagged
- `getStates()`: Return all question states

Features:
- Visual question grid with color-coded states
- Previous/Next buttons for sequential navigation
- Active question highlighted
- Legend showing state meanings
- Responsive grid layout

#### ExamTimer Class
Constructor options:
- `containerId`: Timer display container
- `totalSeconds`: Duration in seconds
- `onTimeUp`: Callback when time expires
- `warningThreshold`: When to show warning (default 5 min)

Methods:
- `start()`: Start countdown
- `stop()`: Stop countdown
- `addTime(seconds)`: Add extra time
- `getRemainingTime()`: Get remaining seconds

Features:
- MM:SS format display
- Warning color at 5 minutes
- Danger color at 1 minute
- Pulse animation when < 1 minute

#### FlagManager Class
Constructor options:
- `containerId`: Container for flagged list
- `flaggedQuestions`: Array of flagged question numbers
- `onFlaggedClick`: Callback when flagged question clicked

Methods:
- `toggleFlag(questionNum)`: Toggle flag status
- `isFlagged(questionNum)`: Check if flagged
- `getFlagged()`: Get all flagged questions
- `render()`: Display flagged list

### 7. Navigator Styling (static/css/cbt-navigator.css)

Comprehensive CSS for:
- Question grid layout (auto-fit columns, smooth transitions)
- Question state colors:
  - Green for answered
  - Orange for unanswered
  - Pink for flagged
- Timer display with warning/danger states
- Flagged questions list with hover effects
- Responsive design (tablets, phones)
- Sticky positioning for sidebar
- Animation effects (pulse warning)

## Key Features

### 1. Deterministic Randomization
- Uses MD5 hash of attempt UUID + salt
- Same UUID always produces same random order
- Allows student to refresh without changing question order
- Consistent across multiple access attempts

### 2. Difficulty/Topic Balancing
- Optional balancing when selecting random questions
- Can be configured per exam
- Ensures representative mix of topics/difficulty levels

### 3. Question State Tracking
- StudentAttemptQuestion tracks each question's state
- States: answered, unanswered, flagged
- Enables question navigator visual indicators

### 4. Exam Behavior Configuration
- `allow_navigation`: Show question grid
- `one_at_a_time`: Show one question per page
- `show_instant_results`: Show if correct/incorrect immediately
- `show_corrections`: Show explanation after submit
- `allow_review`: Return to previous answers

### 5. Question Bank Reusability
- Questions stored independently of exams
- Can be used across multiple exams
- Clone functionality for variants
- Categorization enables smart filtering

## Database Migrations

Created migration: `cbt/migrations/0002_*`
- Creates QuestionBank model
- Creates StudentAttemptQuestion model
- Adds new fields to CBTExam and CBTQuestion
- Adds indexes on frequently searched fields (topic)

## Usage Flow

### For Teachers

1. Create Question Bank
   - Navigate to `/teacher/cbt/question-banks/`
   - Click "Create New Bank"
   - Specify subject, class, term
   - Save bank

2. Add Questions to Bank
   - View bank detail page
   - Click "Add Question"
   - Fill prompt, type, marks, categorization
   - Add answer choices (mark correct answer)
   - Save question

3. Search/Filter Questions
   - Use search box by prompt text
   - Filter by difficulty level
   - Filter by question type
   - Or clone existing questions

4. Create Exam from Question Bank
   - Create CBTExam
   - Select "Random Selection" mode
   - Link to Question Bank
   - Configure randomization settings
   - Specify total_questions_to_display
   - Enable balancing if desired

### For Students

1. Start Exam
   - Questions loaded in randomized order
   - Each student gets unique order (deterministic)
   - Questions never change on refresh

2. Navigate Questions
   - View question grid (if allowed)
   - See answered/unanswered/flagged indicators
   - Click question number to jump
   - Use Previous/Next buttons

3. Manage Time
   - Timer displays remaining time
   - Warning at 5 minutes
   - Danger alert at < 1 minute

4. Flag Questions
   - Flag questions for later review
   - View flagged list in sidebar
   - Click flagged to jump to question

5. Submit Exam
   - Answer tracking ensures all answers saved
   - Submit button finalizes responses

## Database Schema

### QuestionBank
```
id (PK)
name (VARCHAR 180)
subject_id (FK to exams.Subject)
school_class_id (FK to school_classes.SchoolClasses, nullable)
term_id (FK to exams.Term, nullable)
description (TEXT)
created_by_id (FK to auth.User, nullable)
created_at (DATETIME auto_now_add)
updated_at (DATETIME auto_now)
```

### CBTExam (Enhanced)
```
question_mode (VARCHAR 16) DEFAULT 'manual'
question_bank_id (FK to QuestionBank, nullable)
randomize_questions (BOOLEAN) DEFAULT False
randomize_answers (BOOLEAN) DEFAULT False
allow_navigation (BOOLEAN) DEFAULT True
one_at_a_time (BOOLEAN) DEFAULT False
show_instant_results (BOOLEAN) DEFAULT False
show_corrections (BOOLEAN) DEFAULT False
allow_review (BOOLEAN) DEFAULT True
total_questions_to_display (POSITIVE INT, nullable)
balance_by_difficulty (BOOLEAN) DEFAULT False
balance_by_topic (BOOLEAN) DEFAULT False
```

### CBTQuestion (Enhanced)
```
question_bank_id (FK to QuestionBank, nullable)
topic (VARCHAR 100) - indexed
difficulty (VARCHAR 16) DEFAULT 'medium'
created_at (DATETIME auto_now_add)
```

### StudentAttemptQuestion
```
id (PK)
attempt_id (FK to CBTStudentAttempt)
question_id (FK to CBTQuestion)
randomized_position (POSITIVE INT)
randomized_choice_order (TEXT) - JSON array
is_answered (BOOLEAN) DEFAULT False
is_flagged (BOOLEAN) DEFAULT False
created_at (DATETIME auto_now_add)
unique_together: (attempt, question)
```

## Testing Checklist

- [ ] Question bank CRUD operations
- [ ] Search/filter questions by topic, difficulty
- [ ] Clone question functionality
- [ ] Random question selection (verify same order on refresh)
- [ ] Difficulty/topic balancing
- [ ] Choice order randomization
- [ ] Question state tracking
- [ ] Navigator UI with state indicators
- [ ] Timer countdown and warnings
- [ ] Flag manager functionality
- [ ] Access control (only creator can edit)
- [ ] Admin interface operations
- [ ] API search endpoint

## Future Enhancements

1. Bulk import/export questions (CSV)
2. AI-powered question generation
3. Advanced analytics on question difficulty
4. Question versioning and history
5. Collaborative question creation
6. Question difficulty auto-calibration
7. Student performance analytics per question
8. Question bank statistics dashboard
9. Multi-language support for questions
10. Multimedia support (images, videos)

## Files Changed/Created

### Created Files
- `cbt/question_bank_views.py`: Question bank management views (370+ lines)
- `cbt/templates/cbt/question_bank_list.html`: Bank listing with search/filter
- `cbt/templates/cbt/question_bank_form.html`: Bank creation/editing
- `cbt/templates/cbt/question_bank_detail.html`: Bank detail with questions
- `cbt/templates/cbt/question_form.html`: Question CRUD form
- `cbt/templates/cbt/question_confirm_delete.html`: Deletion confirmation
- `cbt/templates/cbt/question_bank_confirm_delete.html`: Bank deletion confirmation
- `static/js/cbt-navigator.js`: Navigator, timer, flag manager classes
- `static/css/cbt-navigator.css`: Navigator and timer styling

### Modified Files
- `cbt/models.py`: Added QuestionBank, StudentAttemptQuestion, enhanced existing models
- `cbt/services.py`: Added randomization functions
- `cbt/forms.py`: Added QuestionBankForm, enhanced CBTExamForm
- `cbt/admin.py`: Enhanced admin interfaces for new models
- `cbt/teacher_urls.py`: Added question bank URL patterns

### Database Migrations
- `cbt/migrations/0002_*`: Creates new models and fields

## Total Lines of Code Added
- Python: ~900 lines (models, views, forms, services)
- Templates: ~600 lines (HTML/Django template)
- JavaScript: ~400 lines (navigator classes)
- CSS: ~300 lines (styling)
- SQL: ~50 lines (migration)
