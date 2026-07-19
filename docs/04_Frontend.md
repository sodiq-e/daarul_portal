# 04. Frontend Documentation

## Frontend Strategy
The frontend is primarily server-rendered Django templates styled with Bootstrap and custom CSS. The design is functional and modular rather than highly componentized.

## Base Layout
Location: templates/base.html

Responsibilities:
- shared navigation and layout shell
- theme variables and global styling hooks
- toast/message rendering
- print-friendly style rules
- shared JavaScript inclusion

## Main Template Areas
- templates/accounts: login, profile, password reset
- templates/students: student management and admissions
- templates/results: report cards, class results, broadsheets
- templates/teachers: teacher-specific portals and forms
- templates/exams: subject and exam paper interfaces
- templates/payroll: invoices and payroll views
- templates/attendance: attendance marking and reporting
- templates/communication: contact and admin messaging

## JavaScript Assets
- static/js/animations.js: site animations and UI animation helpers
- static/js/cbt-navigator.js: CBT navigation and exam UI support

## CSS Assets
- static/css/animations.css: animation layer and transitions
- static/css/animation-utilities.css: utility classes for animation behaviors
- static/css/cbt-navigator.css: CBT-specific styling

## Frontend Patterns
- Forms are rendered directly with Django form widgets
- Tables and cards are used heavily for list pages
- Some views include modal-like UI and simple interactive filtering
- The results page uses Chart.js for visual performance charting

## Results Page Frontend Flow
1. User selects filters from the report card page
2. GET parameters are submitted to the view
3. The server computes filtered datasets
4. The template renders the chart and summary cards
5. JavaScript initializes Chart.js with labels and data from the page context

## Student Portal Frontend
The student portal uses dedicated templates under templates/students/portal/ for:
- dashboard
- profile
- results
- fees
- attendance
- announcements
- timetable
- teacher contact

## Print-Friendly Frontend
- Print templates are present under templates/print/
- Some modules render printable HTML that can be converted to PDF

## Frontend Observations
- Mixed UI generation patterns exist because of long-term feature growth
- The experience is mostly functional and template-driven
- Navigation and visual polish are largely achieved through shared base styles and custom CSS
