from decimal import Decimal
from datetime import date

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from exams.models import Term
from payroll.forms import StudentPaymentForm
from payroll.models import SchoolFee, StudentInvoice, StudentPayment
from settingsapp.models import Tenant
from settingsapp.tenant_utils import set_current_tenant, clear_current_tenant
from students.models import Student
from accounts.models import Profile


class StudentPaymentAllocationTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Test Tenant', slug='test-tenant')
        self.student = Student.objects.create(
            tenant=self.tenant,
            admission_no='STD-001',
            surname='Doe',
            other_names='Jane',
        )
        self.term = Term.objects.create(
            tenant=self.tenant,
            name='first',
            display_name='First Term',
            academic_year='2024/2025',
            start_date=date(2024, 9, 1),
            end_date=date(2024, 12, 15),
            is_active=True,
        )

    def test_invoice_status_changes_to_paid_when_payment_matches_invoice(self):
        fee = SchoolFee.objects.create(tenant=self.tenant, name='School Fees', amount=Decimal('40000.00'))
        invoice = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('40000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )

        payment = StudentPayment.objects.create(
            tenant=self.tenant,
            student=self.student,
            invoice=invoice,
            amount=Decimal('40000.00'),
            payment_date=date(2024, 9, 10),
            payment_method='Cash',
            reference='REF-001',
            invoices=[invoice.id],
            allocations=[{'invoice_id': invoice.id, 'amount_applied': '40000.00'}],
        )

        invoice.refresh_from_db()

        self.assertEqual(payment.invoices, [invoice.id])
        self.assertEqual(invoice.total_paid, Decimal('40000.00'))
        self.assertEqual(invoice.balance, Decimal('0.00'))
        self.assertEqual(invoice.status, 'paid')

    def test_payment_can_cover_multiple_invoices(self):
        fee_1 = SchoolFee.objects.create(tenant=self.tenant, name='School Fees', amount=Decimal('40000.00'))
        fee_2 = SchoolFee.objects.create(tenant=self.tenant, name='Uniform', amount=Decimal('10000.00'))
        fee_3 = SchoolFee.objects.create(tenant=self.tenant, name='Exam Fee', amount=Decimal('5000.00'))

        invoice_1 = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee_1,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('40000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        invoice_2 = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee_2,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('10000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        invoice_3 = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee_3,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('5000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )

        payment = StudentPayment.objects.create(
            tenant=self.tenant,
            student=self.student,
            invoice=invoice_1,
            amount=Decimal('42000.00'),
            payment_date=date(2024, 9, 10),
            payment_method='Bank Transfer',
            reference='REF-002',
            invoices=[invoice_1.id, invoice_2.id, invoice_3.id],
            allocations=[
                {'invoice_id': invoice_1.id, 'amount_applied': '40000.00'},
                {'invoice_id': invoice_2.id, 'amount_applied': '2000.00'},
            ],
        )

        invoice_1.refresh_from_db()
        invoice_2.refresh_from_db()
        invoice_3.refresh_from_db()

        self.assertEqual(payment.invoices, [invoice_1.id, invoice_2.id, invoice_3.id])
        self.assertEqual(invoice_1.status, 'paid')
        self.assertEqual(invoice_2.status, 'overdue')
        self.assertEqual(invoice_3.status, 'overdue')
        self.assertEqual(payment.remaining_balance, Decimal('0.00'))

    def test_payment_form_accepts_multi_invoice_selection_without_single_invoice_choice(self):
        fee_1 = SchoolFee.objects.create(tenant=self.tenant, name='School Fees', amount=Decimal('40000.00'))
        fee_2 = SchoolFee.objects.create(tenant=self.tenant, name='Uniform', amount=Decimal('10000.00'))

        invoice_1 = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee_1,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('40000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        invoice_2 = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee_2,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('10000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )

        form = StudentPaymentForm(data={
            'amount': '42000.00',
            'payment_date': '2024-09-10',
            'payment_method': 'Bank Transfer',
            'reference': 'REF-003',
            'notes': 'Multi-invoice payment',
            'invoices': [str(invoice_1.id), str(invoice_2.id)],
        })

        self.assertTrue(form.is_valid(), form.errors)
        payment = form.save()

        invoice_1.refresh_from_db()
        invoice_2.refresh_from_db()

        self.assertEqual(payment.invoice_id, invoice_1.id)
        self.assertEqual(payment.invoices, [invoice_1.id, invoice_2.id])
        self.assertEqual(invoice_1.total_paid, Decimal('40000.00'))
        self.assertEqual(invoice_1.status, 'paid')
        self.assertEqual(invoice_2.total_paid, Decimal('2000.00'))
        self.assertEqual(invoice_2.status, 'overdue')
        self.assertEqual(invoice_2.balance, Decimal('8000.00'))

    def test_payment_form_shows_student_wallet_balance_separately_from_invoice_list(self):
        fee_1 = SchoolFee.objects.create(tenant=self.tenant, name='School Fees', amount=Decimal('40000.00'))
        fee_2 = SchoolFee.objects.create(tenant=self.tenant, name='Uniform', amount=Decimal('15000.00'))
        invoice_1 = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee_1,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('40000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        invoice_2 = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee_2,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('15000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        StudentPayment.objects.create(
            tenant=self.tenant,
            student=self.student,
            invoice=invoice_1,
            amount=Decimal('50000.00'),
            payment_date=date(2024, 9, 10),
            payment_method='Cash',
            reference='REF-WALLET',
            invoices=[invoice_1.id],
            allocations=[{'invoice_id': invoice_1.id, 'amount_applied': '50000.00'}],
            remaining_balance=Decimal('10000.00'),
        )

    def test_payment_form_restricts_invoice_choices_to_unpaid_invoices_when_wallet_is_selected(self):
        fee_1 = SchoolFee.objects.create(tenant=self.tenant, name='School Fees', amount=Decimal('40000.00'))
        fee_2 = SchoolFee.objects.create(tenant=self.tenant, name='Uniform', amount=Decimal('15000.00'))
        invoice_1 = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee_1,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('40000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        invoice_2 = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee_2,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('15000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        StudentPayment.objects.create(
            tenant=self.tenant,
            student=self.student,
            invoice=invoice_2,
            amount=Decimal('50000.00'),
            payment_date=date(2024, 9, 10),
            payment_method='Cash',
            reference='REF-PAID-INVOICE',
            invoices=[invoice_2.id],
            allocations=[{'invoice_id': invoice_2.id, 'amount_applied': '50000.00'}],
            remaining_balance=Decimal('10000.00'),
        )

        form = StudentPaymentForm(data={
            'amount': '6000.00',
            'payment_date': '2024-09-12',
            'payment_method': 'Wallet',
            'reference': 'REF-WALLET-USE',
            'notes': 'Use wallet for invoice',
            'invoices': [str(invoice_1.id)],
            'apply_remaining_to': str(self.student.pk),
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            [choice[0] for choice in form.fields['invoices'].choices],
            [str(invoice_1.id)],
        )
        self.assertNotIn(invoice_2.pk, [invoice.pk for invoice in form.fields['invoice'].queryset])
        self.assertNotIn(str(invoice_2.id), [choice[0] for choice in form.fields['invoices'].choices])

        form = StudentPaymentForm()
        wallet_choice = next(iter(form.fields['apply_remaining_to'].queryset), None)
        self.assertIsNotNone(wallet_choice)
        self.assertEqual(wallet_choice.pk, self.student.pk)
        self.assertTrue(form.fields['invoice'].queryset.exists())
        self.assertTrue(form.fields['invoices'].choices)
        self.assertNotIn(invoice_2.pk, [invoice.pk for invoice in form.fields['invoice'].queryset])

    def test_payment_form_allows_wallet_balance_to_cover_another_students_unpaid_invoice(self):
        second_student = Student.objects.create(
            tenant=self.tenant,
            admission_no='STD-002',
            surname='Smith',
            other_names='Alice',
        )
        fee = SchoolFee.objects.create(tenant=self.tenant, name='School Fees', amount=Decimal('40000.00'))
        invoice = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=second_student,
            fee=fee,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('15000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        StudentPayment.objects.create(
            tenant=self.tenant,
            student=self.student,
            invoice=StudentInvoice.objects.create(
                tenant=self.tenant,
                student=self.student,
                fee=fee,
                issued_date=date(2024, 9, 2),
                due_date=date(2024, 9, 30),
                amount_due=Decimal('40000.00'),
                academic_session='2024/2025',
                term=self.term,
                status='pending',
            ),
            amount=Decimal('50000.00'),
            payment_date=date(2024, 9, 10),
            payment_method='Bank Transfer',
            reference='REF-WALLET-SOURCE',
            invoices=[StudentInvoice.objects.filter(student=self.student).first().id],
            allocations=[{'invoice_id': StudentInvoice.objects.filter(student=self.student).first().id, 'amount_applied': '40000.00'}],
            remaining_balance=Decimal('10000.00'),
        )

        form = StudentPaymentForm(data={
            'amount': '6000.00',
            'payment_date': '2024-09-12',
            'payment_method': 'Wallet',
            'reference': 'REF-WALLET-USE-OTHER-STUDENT',
            'notes': 'Use wallet for another student invoice',
            'invoice': str(invoice.id),
            'invoices': [str(invoice.id)],
            'apply_remaining_to': str(self.student.pk),
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn(str(invoice.id), [choice[0] for choice in form.fields['invoices'].choices])

    def test_wallet_source_student_stays_in_available_wallets_when_covering_another_students_invoice(self):
        second_student = Student.objects.create(
            tenant=self.tenant,
            admission_no='STD-002',
            surname='Smith',
            other_names='Alice',
        )
        fee = SchoolFee.objects.create(tenant=self.tenant, name='School Fees', amount=Decimal('40000.00'))
        invoice = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=second_student,
            fee=fee,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('15000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        source_payment = StudentPayment.objects.create(
            tenant=self.tenant,
            student=self.student,
            invoice=StudentInvoice.objects.create(
                tenant=self.tenant,
                student=self.student,
                fee=fee,
                issued_date=date(2024, 9, 2),
                due_date=date(2024, 9, 30),
                amount_due=Decimal('40000.00'),
                academic_session='2024/2025',
                term=self.term,
                status='pending',
            ),
            amount=Decimal('15000.00'),
            payment_date=date(2024, 9, 10),
            payment_method='Bank Transfer',
            reference='REF-WALLET-SOURCE-KEEP',
            invoices=[StudentInvoice.objects.filter(student=self.student).first().id],
            allocations=[{'invoice_id': StudentInvoice.objects.filter(student=self.student).first().id, 'amount_applied': '15000.00'}],
            remaining_balance=Decimal('15000.00'),
        )

        form = StudentPaymentForm(data={
            'amount': '6000.00',
            'payment_date': '2024-09-12',
            'payment_method': 'Wallet',
            'reference': 'REF-WALLET-TRANSFER-KEEP',
            'notes': 'Use wallet for another student invoice',
            'invoice': str(invoice.id),
            'invoices': [str(invoice.id)],
            'apply_remaining_to': str(self.student.pk),
        })

        self.assertTrue(form.is_valid(), form.errors)
        payment = form.save()

        self.student.refresh_from_db()
        self.assertEqual(payment.student_id, self.student.pk)
        self.assertEqual(self.student.wallet_balance, Decimal('9000.00'))
        self.assertIn(self.student.pk, [student.pk for student in StudentPaymentForm().fields['apply_remaining_to'].queryset])
        source_payment.refresh_from_db()
        self.assertEqual(source_payment.remaining_balance, Decimal('9000.00'))

    def test_payment_form_hides_paid_invoices_and_shows_only_unpaid_balances(self):
        fee = SchoolFee.objects.create(tenant=self.tenant, name='School Fees', amount=Decimal('40000.00'))
        paid_invoice = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('40000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        StudentPayment.objects.create(
            tenant=self.tenant,
            student=self.student,
            invoice=paid_invoice,
            amount=Decimal('40000.00'),
            payment_date=date(2024, 9, 10),
            payment_method='Cash',
            reference='REF-PAID',
            invoices=[paid_invoice.id],
            allocations=[{'invoice_id': paid_invoice.id, 'amount_applied': '40000.00'}],
        )

        form = StudentPaymentForm()
        self.assertNotIn(paid_invoice.id, [invoice.pk for invoice in form.fields['invoice'].queryset])
        self.assertNotIn(paid_invoice.id, [int(value) for value, label in form.fields['invoices'].choices if value])
        self.assertNotIn(paid_invoice.id, [invoice.pk for invoice in form.fields['apply_remaining_to'].queryset])

    def test_payment_form_splits_amount_across_students_when_selected_invoices_span_multiple_students(self):
        second_student = Student.objects.create(
            tenant=self.tenant,
            admission_no='STD-002',
            surname='Smith',
            other_names='John',
        )
        fee_1 = SchoolFee.objects.create(tenant=self.tenant, name='School Fees', amount=Decimal('60000.00'))
        fee_2 = SchoolFee.objects.create(tenant=self.tenant, name='Uniform', amount=Decimal('50000.00'))

        invoice_1 = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee_1,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('60000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        invoice_2 = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=second_student,
            fee=fee_2,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('50000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )

        form = StudentPaymentForm(data={
            'amount': '90000.00',
            'payment_date': '2024-09-10',
            'payment_method': 'Bank Transfer',
            'reference': 'REF-005',
            'notes': 'Split across two students',
            'invoices': [str(invoice_1.id), str(invoice_2.id)],
        })

        self.assertTrue(form.is_valid(), form.errors)
        payment = form.save()

        self.assertIsNotNone(payment)
        self.assertEqual(StudentPayment.objects.filter(student__in=[self.student, second_student]).count(), 2)
        self.assertEqual(StudentPayment.objects.get(student=self.student).amount, Decimal('60000.00'))
        self.assertEqual(StudentPayment.objects.get(student=second_student).amount, Decimal('30000.00'))
        self.assertEqual(invoice_1.refresh_status(), 'paid')
        self.assertEqual(invoice_2.refresh_status(), 'overdue')

    def test_wallet_usage_does_not_count_as_school_collected_and_rejects_insufficient_wallet(self):
        fee = SchoolFee.objects.create(tenant=self.tenant, name='School Fees', amount=Decimal('40000.00'))
        invoice = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('40000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        wallet_payment = StudentPayment.objects.create(
            tenant=self.tenant,
            student=self.student,
            invoice=invoice,
            amount=Decimal('20000.00'),
            payment_date=date(2024, 9, 10),
            payment_method='Wallet',
            reference='REF-WALLET-EXISTING',
            invoices=[invoice.id],
            allocations=[{'invoice_id': invoice.id, 'amount_applied': '20000.00'}],
            remaining_balance=Decimal('20000.00'),
            wallet_used=True,
            wallet_applied=Decimal('20000.00'),
        )

        self.assertEqual(wallet_payment.cash_received, Decimal('0.00'))
        self.assertEqual(wallet_payment.school_income_amount, Decimal('0.00'))

        form = StudentPaymentForm(data={
            'amount': '50000.00',
            'payment_date': '2024-09-11',
            'payment_method': 'Wallet',
            'reference': 'REF-INSUFFICIENT',
            'notes': 'Wallet should not be sufficient',
            'invoices': [str(invoice.id)],
            'apply_remaining_to': str(self.student.pk),
        })

        self.assertFalse(form.is_valid())
        self.assertIn('apply_remaining_to', form.errors)

    def test_invoice_total_paid_counts_wallet_payment_from_another_student(self):
        wallet_source = Student.objects.create(
            tenant=self.tenant,
            admission_no='STD-003',
            surname='Johnson',
            other_names='Mary',
        )
        fee = SchoolFee.objects.create(tenant=self.tenant, name='School Fees', amount=Decimal('40000.00'))
        invoice = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('60000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )

        wallet_payment = StudentPayment.objects.create(
            tenant=self.tenant,
            student=wallet_source,
            invoice=invoice,
            amount=Decimal('20000.00'),
            payment_date=date(2024, 9, 12),
            payment_method='Wallet',
            reference='REF-WALLET-CROSS-STUDENT',
            invoices=[invoice.id],
            allocations=[{'invoice_id': invoice.id, 'amount_applied': '20000.00'}],
            remaining_balance=Decimal('0.00'),
            wallet_used=True,
            wallet_applied=Decimal('20000.00'),
        )

        self.assertEqual(invoice.total_paid, Decimal('20000.00'))
        self.assertEqual(invoice.balance, Decimal('40000.00'))
        self.assertEqual(wallet_payment.school_income_amount, Decimal('0.00'))

    def test_student_net_amount_owing_excludes_wallet_credit(self):
        fee = SchoolFee.objects.create(tenant=self.tenant, name='School Fees', amount=Decimal('40000.00'))
        invoice = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('50000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        StudentPayment.objects.create(
            tenant=self.tenant,
            student=self.student,
            invoice=invoice,
            amount=Decimal('25000.00'),
            payment_date=date(2024, 9, 10),
            payment_method='Bank Transfer',
            reference='REF-WALLET-CREDIT',
            invoices=[invoice.id],
            allocations=[{'invoice_id': invoice.id, 'amount_applied': '25000.00'}],
            remaining_balance=Decimal('25000.00'),
        )

        self.assertEqual(self.student.wallet_balance, Decimal('25000.00'))
        self.assertEqual(self.student.net_amount_owing, Decimal('25000.00'))

    def test_wallet_balance_is_deducted_when_used_and_returned_cash_reduces_wallet(self):
        fee = SchoolFee.objects.create(tenant=self.tenant, name='School Fees', amount=Decimal('40000.00'))
        wallet_invoice = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('40000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        invoice = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee,
            issued_date=date(2024, 9, 3),
            due_date=date(2024, 10, 5),
            amount_due=Decimal('25000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        original = StudentPayment.objects.create(
            tenant=self.tenant,
            student=self.student,
            invoice=wallet_invoice,
            amount=Decimal('50000.00'),
            payment_date=date(2024, 9, 1),
            payment_method='Bank Transfer',
            reference='REF-ORIG',
            invoices=[wallet_invoice.id],
            allocations=[{'invoice_id': wallet_invoice.id, 'amount_applied': '40000.00'}],
            remaining_balance=Decimal('10000.00'),
        )

        self.assertEqual(self.student.wallet_balance, Decimal('10000.00'))

        form = StudentPaymentForm(data={
            'amount': '6000.00',
            'payment_date': '2024-09-12',
            'payment_method': 'Wallet',
            'reference': 'REF-WALLET-USE',
            'notes': 'Use wallet for invoice',
            'invoices': [str(invoice.id)],
            'apply_remaining_to': str(self.student.pk),
        })

        self.assertTrue(form.is_valid(), form.errors)
        payment = form.save()
        original.refresh_from_db()
        self.student.refresh_from_db()

        self.assertEqual(original.remaining_balance, Decimal('4000.00'))
        self.assertEqual(self.student.wallet_balance, Decimal('4000.00'))
        self.assertEqual(payment.wallet_applied, Decimal('6000.00'))

        refund_form = StudentPaymentForm(data={
            'amount': '2000.00',
            'payment_date': '2024-09-13',
            'payment_method': 'Wallet Refund',
            'reference': 'REF-WALLET-REFUND',
            'notes': 'Return cash to student',
            'invoices': [str(invoice.id)],
            'apply_remaining_to': str(self.student.pk),
        })

        self.assertTrue(refund_form.is_valid(), refund_form.errors)
        refund = refund_form.save()
        self.student.refresh_from_db()

        self.assertEqual(refund.wallet_refund_amount, Decimal('2000.00'))
        self.assertEqual(self.student.wallet_balance, Decimal('2000.00'))

    def test_print_receipts_page_renders_card_summary_and_table(self):
        fee = SchoolFee.objects.create(tenant=self.tenant, name='School Fees', amount=Decimal('40000.00'))
        invoice = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('40000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        StudentPayment.objects.create(
            tenant=self.tenant,
            student=self.student,
            invoice=invoice,
            amount=Decimal('20000.00'),
            payment_date=date(2024, 9, 10),
            payment_method='Cash',
            reference='REF-004',
            invoices=[invoice.id],
            allocations=[{'invoice_id': invoice.id, 'amount_applied': '20000.00'}],
        )

        group, _ = Group.objects.get_or_create(name='Staff')
        user = User.objects.create_user(username='staffuser', password='pass1234')
        user.profile.requested_group = 'Staff'
        user.profile.is_approved = True
        user.profile.save()
        user.groups.add(group)

        self.client.force_login(user)
        response = self.client.get(reverse('print_receipts'))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('Print Receipts', content)
        self.assertIn('Total Due', content)
        self.assertIn('Outstanding Balance', content)
        self.assertIn('<table class="table table-striped">', content)
        self.assertIn('School Fees', content)

    def test_payment_batch_splits_across_students_and_keeps_outstanding_balance(self):
        second_student = Student.objects.create(
            tenant=self.tenant,
            admission_no='STD-002',
            surname='Smith',
            other_names='Alice',
        )

        fee_1 = SchoolFee.objects.create(tenant=self.tenant, name='School Fees', amount=Decimal('60000.00'))
        fee_2 = SchoolFee.objects.create(tenant=self.tenant, name='Uniform', amount=Decimal('70000.00'))

        invoice_1 = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=self.student,
            fee=fee_1,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('60000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )
        invoice_2 = StudentInvoice.objects.create(
            tenant=self.tenant,
            student=second_student,
            fee=fee_2,
            issued_date=date(2024, 9, 2),
            due_date=date(2024, 9, 30),
            amount_due=Decimal('70000.00'),
            academic_session='2024/2025',
            term=self.term,
            status='pending',
        )

        form = StudentPaymentForm(data={
            'amount': '90000.00',
            'payment_date': '2024-09-10',
            'payment_method': 'Bank Transfer',
            'reference': 'REF-BATCH-001',
            'notes': 'Multi-student payment batch',
            'invoices': [str(invoice_1.id), str(invoice_2.id)],
        })

        self.assertTrue(form.is_valid(), form.errors)
        payment = form.save()

        payments = StudentPayment.objects.filter(student__in=[self.student, second_student]).order_by('student_id')
        self.assertEqual(payments.count(), 2)
        self.assertEqual(sum(payment.amount for payment in payments), Decimal('90000.00'))
        self.assertEqual(payment.student_id, self.student.id)

        invoice_1.refresh_from_db()
        invoice_2.refresh_from_db()
        self.assertEqual(invoice_1.balance, Decimal('0.00'))
        self.assertEqual(invoice_2.balance, Decimal('40000.00'))

    def test_multi_fee_invoice_creation_persists_for_active_tenant(self):
        fee_1 = SchoolFee.objects.create(tenant=self.tenant, name='School Fees', amount=Decimal('40000.00'))
        fee_2 = SchoolFee.objects.create(tenant=self.tenant, name='Uniform', amount=Decimal('10000.00'))

        group, _ = Group.objects.get_or_create(name='Staff')
        user = User.objects.create_user(username='staffuser2', password='pass1234')
        user.profile.requested_group = 'Staff'
        user.profile.is_approved = True
        user.profile.save()
        user.groups.add(group)

        self.client.force_login(user)
        set_current_tenant(self.tenant)
        try:
            response = self.client.post(reverse('invoice_add'), {
                'student': self.student.pk,
                'fees': [fee_1.pk, fee_2.pk],
                'academic_session': '2024/2025',
                'term': self.term.pk,
                'issued_date': '2024-09-02',
                'due_date': '2024-09-30',
                'status': 'pending',
                'notes': 'Multi-fee invoice batch',
            })
        finally:
            clear_current_tenant()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            StudentInvoice.objects.filter(student=self.student, tenant=self.tenant).count(),
            2,
        )
