# 13. Payroll Module

## Feature Overview
The payroll module manages school expenses, fee types, invoices, payments, and payroll dashboards.

## Core Features

### Payroll Dashboard
- Entry point: /payroll/
- View: PayrollDashboardView
- Template: templates/payroll/dashboard.html

Responsibilities:
- show totals for expenses, invoices, payments
- calculate outstanding balances
- show recent invoices, payments, and expenses

### Expense Management
- View: SchoolExpenseListView, SchoolExpenseCreateView
- Model: SchoolExpense
- Template: templates/payroll/expense_list.html, expense_form.html

### Fee Type Management
- Views: SchoolFeeListView, SchoolFeeCreateView, SchoolFeeUpdateView, SchoolFeeDeleteView
- Model: SchoolFee

### Student Invoices and Payments
- Views: StudentInvoiceListView, print_invoices, print_receipts, StudentPayment-related views
- Models: StudentInvoice, StudentPayment

Workflow:
1. Staff creates fee types and invoices
2. Student invoices are filtered by academic session, term, and student
3. Payments are recorded against invoices
4. Outstanding balances are recalculated
5. Printable invoices and receipts are generated

## Validation Rules
- Invoice lists can be filtered by academic session, term, and student
- Balances depend on total amount due and total payments

## Permission Checks
- Staff/teacher/admin-like accounts can manage payroll according to staff_can_manage

## Dependencies
- Depends on students and exams.Term
