from django.contrib import admin
from .models import Staff, Payslip, SchoolExpense, SalaryComponent, PayrollDashboard


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('name', 'staff_type', 'role', 'basic', 'is_active', 'teacher')
    list_filter = ('staff_type', 'is_active', 'date_joined')
    search_fields = ('name', 'employee_id', 'email')
    readonly_fields = ('date_joined',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('teacher__user')


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ('staff', 'month', 'basic_salary', 'total_allowances', 'total_deductions', 'net', 'is_processed')
    list_filter = ('is_processed', 'month', 'processed_by')
    search_fields = ('staff__name', 'staff__employee_id')
    date_hierarchy = 'month'
    readonly_fields = ('processed_at', 'basic_salary', 'total_allowances', 'total_deductions')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('staff', 'processed_by')


@admin.register(SalaryComponent)
class SalaryComponentAdmin(admin.ModelAdmin):
    list_display = ('staff', 'component_type', 'name', 'amount', 'is_active', 'effective_date')
    list_filter = ('component_type', 'is_active', 'effective_date')
    search_fields = ('staff__name', 'name')
    autocomplete_fields = ('staff',)


@admin.register(PayrollDashboard)
class PayrollDashboardAdmin(admin.ModelAdmin):
    list_display = ('staff', 'month', 'total_earnings', 'total_deductions', 'net_pay', 'attendance_percentage')
    list_filter = ('month',)
    search_fields = ('staff__name', 'staff__employee_id')
    date_hierarchy = 'month'
    readonly_fields = ('created_at',)


admin.site.register(SchoolExpense)
