from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import models
from settingsapp.models import TenantModel


class Staff(TenantModel):
    STAFF_TYPES = [
        ('teacher', 'Teacher'),
        ('admin', 'Administrator'),
        ('support', 'Support Staff'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_profile'
    )
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


class SalaryComponent(TenantModel):
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


class Payslip(TenantModel):
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


class PayrollDashboard(TenantModel):
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


class SchoolExpense(TenantModel):
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


class SchoolFee(TenantModel):
    name = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    school_classes = models.ManyToManyField(
        'school_classes.SchoolClasses',
        blank=True,
        related_name='school_fees',
        help_text='Students in these classes inherit this fee when creating an invoice.'
    )

    def __str__(self):
        return f"{self.name} ({self.amount})"


class StudentInvoice(TenantModel):
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
    # Optional academic session and term for filtering and reporting
    academic_session = models.CharField(max_length=20, blank=True, help_text='e.g., 2023/2024')
    term = models.ForeignKey('exams.Term', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
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
        return f"Invoice {self.id} - {self.student} - ₦{self.amount_due}"

    def refresh_status(self, as_of_date=None):
        as_of_date = as_of_date or date.today()
        total_paid = self.total_paid
        balance = self.amount_due - total_paid

        if balance <= Decimal('0.00'):
            self.status = 'paid'
        elif self.due_date < as_of_date:
            self.status = 'overdue'
        else:
            self.status = 'pending'
        return self.status

    @property
    def total_paid(self):
        total = Decimal('0.00')
        payment_ids = list(StudentPayment.objects.filter(student_id=self.student_id).values_list('id', flat=True))

        for payment in StudentPayment.objects.filter(id__in=payment_ids).select_related('invoice'):
            if payment.allocations:
                for allocation in payment.allocations:
                    if int(allocation.get('invoice_id')) == self.id:
                        total += Decimal(str(allocation.get('amount_applied', 0)))
            elif payment.invoice_id == self.id:
                total += payment.amount

        if total == Decimal('0.00'):
            for payment in self.payments.all():
                if payment.invoice_id == self.id:
                    total += payment.amount
                elif payment.allocations:
                    for allocation in payment.allocations:
                        if int(allocation.get('invoice_id')) == self.id:
                            total += Decimal(str(allocation.get('amount_applied', 0)))
        return total

    @property
    def balance(self):
        return self.amount_due - self.total_paid

    @property
    def is_owing(self):
        return self.balance > Decimal('0.00')

    def save(self, *args, **kwargs):
        if self.pk:
            self.status = self.refresh_status()
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
            self.status = self.refresh_status()
            super().save(update_fields=['status'])


class StudentPayment(TenantModel):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='payments')
    invoice = models.ForeignKey(StudentInvoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=120, blank=True)
    reference = models.CharField(max_length=200, blank=True)
    invoices = models.JSONField(default=list, blank=True, help_text='List of invoice IDs this payment covered.')
    allocations = models.JSONField(default=list, blank=True, help_text='Allocation details for each invoice covered by the payment.')
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
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
        return f"Payment {self.amount} for {self.student}"

    def _normalize_invoice_ids(self, invoice_ids):
        values = []
        for invoice_id in invoice_ids or []:
            try:
                invoice_pk = int(invoice_id)
            except (TypeError, ValueError):
                continue
            if invoice_pk not in values:
                values.append(invoice_pk)
        return values

    def build_allocations(self, invoice_ids=None):
        selected_ids = self._normalize_invoice_ids(invoice_ids or self.invoices or ([self.invoice_id] if self.invoice_id else []))
        if not selected_ids:
            return []

        selected_invoices = list(StudentInvoice.objects.filter(pk__in=selected_ids).order_by('due_date', 'issued_date'))
        if not selected_invoices and self.invoice_id:
            selected_invoices = [self.invoice]

        remaining_payment = Decimal(str(self.amount or 0))
        allocations = []
        for invoice in selected_invoices:
            available_amount = max(Decimal('0.00'), invoice.amount_due - invoice.total_paid)
            amount_applied = min(remaining_payment, available_amount)
            allocations.append({
                'invoice_id': invoice.pk,
                'amount_applied': str(amount_applied),
                'remaining_balance': str(max(Decimal('0.00'), available_amount - amount_applied)),
            })
            remaining_payment -= amount_applied

        self.remaining_balance = max(Decimal('0.00'), remaining_payment)
        return allocations

    def save(self, *args, **kwargs):
        if self.invoice_id and not self.invoices:
            self.invoices = [self.invoice_id]
        if self.invoice_id and self.invoice_id not in self._normalize_invoice_ids(self.invoices):
            self.invoices = [self.invoice_id, *self._normalize_invoice_ids(self.invoices)]
        self.invoices = self._normalize_invoice_ids(self.invoices)
        if self.invoices and self.invoice_id is None:
            self.invoice_id = self.invoices[0]
        if self.invoice_id and self.student_id is None:
            self.student_id = self.invoice.student_id
        if self.invoices:
            self.allocations = self.build_allocations(self.invoices)
        else:
            self.allocations = []
            self.remaining_balance = Decimal('0.00')

        super().save(*args, **kwargs)

        for invoice_id in self.invoices:
            invoice = StudentInvoice.objects.filter(pk=invoice_id).first()
            if invoice:
                invoice.refresh_status()
                invoice.save(update_fields=['status'])
