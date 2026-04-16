from django.contrib import admin
from .models import Staff, Payslip, SchoolExpense, SchoolFee, StudentInvoice, StudentPayment

admin.site.register(Staff)
admin.site.register(Payslip)
admin.site.register(SchoolExpense)
admin.site.register(SchoolFee)
admin.site.register(StudentInvoice)
admin.site.register(StudentPayment)
