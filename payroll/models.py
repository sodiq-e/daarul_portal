from decimal import Decimal

from django.conf import settings
from django.db import models


class Staff(models.Model):
    STAFF_TYPES = [
        ('teacher', 'Teacher'),
        ('admin', 'Administrator'),
        ('support', 'Support Staff'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    staff_type = models.CharField(max_length=20, choices=STAFF_TYPES, default='other')
    role = models.CharField(max_length=100, blank=True)
    basic = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Link to teacher if applicable
    teacher = models.OneToOneField(
        'school_classes.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payroll_staff'
    )

    # Contact info
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    # Employment details
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    date_joined = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_staff_type_display()})"


class SalaryComponent(models.Model):
    """Components that make up teacher/admin salary"""
    COMPONENT_TYPES = [
        ('basic', 'Basic Salary'),
        ('allowance', 'Allowance'),
        ('bonus', 'Bonus'),
        ('deduction', 'Deduction'),
    ]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='salary_components')
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPES)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField(default=models.functions.Now)

    def __str__(self):
        return f"{self.staff.name} - {self.name}: ₦{self.amount}"


class Payslip(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    month = models.DateField()
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Auto-calculated fields
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Status
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_payslips'
    )

    @property
    def gross(self):
        return self.basic_salary + self.total_allowances

    @property
    def net(self):
        return self.gross - self.total_deductions

    def save(self, *args, **kwargs):
        """Auto-calculate totals from salary components"""
        if not self.is_processed:
            # Calculate basic salary
            self.basic_salary = self.staff.basic

            # Calculate allowances and deductions from components
            components = SalaryComponent.objects.filter(
                staff=self.staff,
                is_active=True,
                effective_date__lte=self.month
            )

            self.total_allowances = sum(
                comp.amount for comp in components
                if comp.component_type in ['allowance', 'bonus']
            )

            self.total_deductions = sum(
                comp.amount for comp in components
                if comp.component_type == 'deduction'
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.staff.name} - {self.month.strftime('%B %Y')}"


class PayrollDashboard(models.Model):
    """Dashboard data for payroll overview"""
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    month = models.DateField()
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Summary data
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    performance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('staff', 'month')

    def __str__(self):
        return f"{self.staff.name} - {self.month.strftime('%B %Y')} Dashboard"


class SchoolExpense(models.Model):
    date = models.DateField()
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=120, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='school_expenses'
    )

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.description[:50]}"


class SchoolFee(models.Model):
    name = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.amount})"


class StudentInvoice(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='invoices')
    fee = models.ForeignKey(SchoolFee, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    issued_date = models.DateField()
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_invoices'
    )

    class Meta:
        ordering = ['-issued_date']

    def __str__(self):
        return f"Invoice {self.id} - {self.student.full_name}"

    @property
    def total_paid(self):
        total = self.payments.aggregate(models.Sum('amount'))['amount__sum']
        return total or Decimal('0.00')

    @property
    def balance(self):
        return self.amount_due - self.total_paid

    @property
    def is_owing(self):
        return self.balance > Decimal('0.00')


class StudentPayment(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='payments')
    invoice = models.ForeignKey(StudentInvoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=120, blank=True)
    reference = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_payments'
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment {self.amount} for {self.student.full_name}"
