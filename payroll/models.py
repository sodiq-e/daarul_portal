from decimal import Decimal

from django.conf import settings
from django.db import models


class Staff(models.Model):
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=100, blank=True)
    basic = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name


class Payslip(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    month = models.DateField()
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def gross(self):
        return self.staff.basic + self.allowances

    @property
    def net(self):
        return self.gross - self.deductions

    def __str__(self):
        return f"{self.staff.name} - {self.month}"


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
