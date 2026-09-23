from decimal import Decimal
from datetime import date

from django.core.management import call_command

from payroll.forms import StudentPaymentForm
from payroll.models import SchoolFee, StudentInvoice, StudentPayment
from students.models import Student
from exams.models import Term
from settingsapp.models import Tenant


def run():
    import django
    django.setup()
    tenant = Tenant.objects.create(name='TmpTenantDebug', slug='tmptenantdebug')
    student = Student.objects.create(tenant=tenant, admission_no='STD-777', surname='Doe', other_names='Jane')
    term = Term.objects.create(tenant=tenant, name='first', display_name='First Term', academic_year='2024/2025', start_date=date(2024,9,1), end_date=date(2024,12,15), is_active=True)
    fee = SchoolFee.objects.create(tenant=tenant, name='School Fees', amount=Decimal('40000.00'))
    invoice = StudentInvoice.objects.create(
        tenant=tenant,
        student=student,
        fee=fee,
        issued_date=date(2024,9,2),
        due_date=date(2024,9,30),
        amount_due=Decimal('40000.00'),
        academic_session='2024/2025',
        term=term,
        status='pending',
    )
    orig = StudentPayment.objects.create(
        tenant=tenant,
        student=student,
        invoice=invoice,
        amount=Decimal('50000.00'),
        payment_date=date(2024,9,1),
        payment_method='Bank Transfer',
        reference='REF-ORIG',
        invoices=[invoice.id],
        allocations=[{'invoice_id': invoice.id, 'amount_applied': '40000.00'}],
        remaining_balance=Decimal('10000.00'),
    )
    print('orig before', orig.remaining_balance, student.wallet_balance)
    form = StudentPaymentForm(data={
        'amount': '6000.00',
        'payment_date': '2024-09-12',
        'payment_method': 'Wallet',
        'reference': 'REF-WALLET-USE',
        'notes': 'Use wallet for invoice',
        'invoices': [str(invoice.id)],
        'apply_remaining_to': str(student.pk),
    })
    print('valid?', form.is_valid(), form.errors)
    if form.is_valid():
        payment = form.save()
        print('wallet_applied', payment.wallet_applied)
        print('wallet_balance after save', student.wallet_balance)
        orig.refresh_from_db()
        print('orig after', orig.remaining_balance)
        print('all', list(StudentPayment.objects.filter(student=student).values_list('id','amount','remaining_balance','wallet_applied','wallet_used','payment_method')))

if __name__ == '__main__':
    run()
