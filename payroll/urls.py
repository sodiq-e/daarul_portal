from django.urls import path
from . import views

urlpatterns = [
    path('', views.PayrollDashboardView.as_view(), name='payroll_dashboard'),
    path('expenses/', views.SchoolExpenseListView.as_view(), name='expense_list'),
    path('expenses/add/', views.SchoolExpenseCreateView.as_view(), name='expense_add'),
    path('fees/', views.SchoolFeeListView.as_view(), name='fee_list'),
    path('fees/add/', views.SchoolFeeCreateView.as_view(), name='fee_add'),
    path('invoices/', views.StudentInvoiceListView.as_view(), name='invoice_list'),
    path('invoices/add/', views.StudentInvoiceCreateView.as_view(), name='invoice_add'),
    path('invoices/<int:pk>/', views.StudentInvoiceDetailView.as_view(), name='invoice_detail'),
    path('payments/add/', views.StudentPaymentCreateView.as_view(), name='payment_add'),
    path('payments/<int:pk>/', views.StudentPaymentDetailView.as_view(), name='payment_detail'),
    path('payments/', views.StudentPaymentListView.as_view(), name='payment_list'),
    
    # Teacher Payroll Views
    path('teacher/payroll/', views.TeacherPayrollView.as_view(), name='teacher_payroll'),
    path('teacher/dashboard/', views.TeacherPayrollDashboardView.as_view(), name='teacher_payroll_dashboard'),
    path('teacher/payslip/<int:pk>/', views.TeacherPayslipDetailView.as_view(), name='teacher_payslip_detail'),
    path('teacher/payslip/<int:pk>/print/', views.teacher_print_payslip, name='teacher_print_payslip'),
]
