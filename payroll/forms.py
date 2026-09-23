from decimal import Decimal

from django import forms

from .models import SchoolExpense, SchoolFee, StudentInvoice, StudentPayment
from exams.models import Term
from students.models import Student


class SchoolExpenseForm(forms.ModelForm):
    class Meta:
        model = SchoolExpense
        fields = ['date', 'description', 'category', 'amount']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class SchoolFeeForm(forms.ModelForm):
    class Meta:
        model = SchoolFee
        fields = ['name', 'amount', 'description', 'school_classes']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'school_classes': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }


class StudentInvoiceForm(forms.ModelForm):
    fees = forms.ModelMultipleChoiceField(
        queryset=SchoolFee.objects.order_by('name'),
        required=True,
        label='Fees',
        help_text='Class fees are selected automatically. Remove any fee that should not apply to this student.'
    )
    academic_session = forms.CharField(max_length=20, required=True, label='Academic Session')
    term = forms.ModelChoiceField(queryset=Term.objects.none(), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['academic_session'].initial = (
            Term.objects.filter(is_active=True).values_list('academic_year', flat=True).first() or ''
        )
        self.fields['term'].queryset = Term.objects.order_by('-is_active', '-academic_year', 'name')
        self.fields['fees'].widget.attrs.update({'class': 'form-select', 'size': 8})
        student_id = self.data.get('student') if self.is_bound else self.initial.get('student')
        if student_id:
            try:
                student = Student.objects.get(pk=student_id)
                self.fields['fees'].initial = SchoolFee.objects.filter(school_classes=student.student_class)
            except (ValueError, TypeError, Student.DoesNotExist):
                pass

    class Meta:
        model = StudentInvoice
        fields = ['student', 'fees', 'academic_session', 'term', 'issued_date', 'due_date', 'status', 'notes']
        widgets = {
            'issued_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('student') and not cleaned_data.get('fees'):
            self.add_error('fees', 'Select at least one fee.')
        return cleaned_data


class InvoiceChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        student_label = obj.student if obj.student else 'Unknown student'
        amount_label = f"₦{obj.amount_due}"
        fee_label = f" ({obj.fee})" if obj.fee else ''
        return f"Invoice {obj.id} - {student_label}{fee_label} - {amount_label}"


class WalletBalanceChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        remaining = Decimal('0.00')
        for payment in obj.payments.all():
            remaining += Decimal(str(payment.remaining_balance or 0))
        return f"{obj.full_name} — Wallet balance: ₦{remaining}"


class StudentPaymentForm(forms.ModelForm):
    invoice = InvoiceChoiceField(
        queryset=StudentInvoice.objects.none(),
        empty_label='Select Invoice (optional when paying multiple invoices)',
        required=False,
    )
    invoices = forms.MultipleChoiceField(
        choices=[],
        required=False,
        label='Invoices Covered',
        widget=forms.CheckboxSelectMultiple,
    )
    apply_remaining_to = WalletBalanceChoiceField(
        queryset=Student.objects.none(),
        required=False,
        empty_label='No leftover balance available',
        label='Student wallet balance to apply (optional)',
        help_text='Choose a student with a leftover balance. This is separate from the invoice list below and is not another invoice option.',
    )

    class Meta:
        model = StudentPayment
        fields = ['invoice', 'invoices', 'amount', 'payment_date', 'payment_method', 'reference', 'notes', 'apply_remaining_to']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].required = False
        all_invoices = StudentInvoice.objects.select_related('student', 'fee').order_by('-issued_date')
        unpaid_invoices = [invoice for invoice in all_invoices if invoice.balance > Decimal('0.00')]
        unpaid_invoice_queryset = StudentInvoice.objects.filter(pk__in=[invoice.pk for invoice in unpaid_invoices]).select_related('student', 'fee').order_by('-issued_date')

        wallet_students = []
        for student in Student.objects.order_by('surname', 'other_names').prefetch_related('payments'):
            wallet_total = sum(
                Decimal(str(payment.remaining_balance or 0))
                for payment in student.payments.all()
                if Decimal(str(payment.remaining_balance or 0)) > Decimal('0.00')
            )
            if wallet_total > Decimal('0.00'):
                wallet_students.append((student.pk, wallet_total))

        wallet_queryset = Student.objects.filter(pk__in=[student_id for student_id, _ in wallet_students]).order_by('surname', 'other_names')

        wallet_student_id = None
        if self.data:
            wallet_student_id = self.data.get('apply_remaining_to')
        elif self.initial.get('apply_remaining_to'):
            wallet_student_id = self.initial.get('apply_remaining_to')

        if wallet_student_id:
            try:
                wallet_student_id = int(wallet_student_id)
            except (TypeError, ValueError):
                wallet_student_id = None

        self.fields['invoice'].queryset = unpaid_invoice_queryset
        self.fields['invoices'].choices = [
            (str(invoice.pk), f"{invoice} — Remaining balance: ₦{invoice.balance}") for invoice in unpaid_invoices
        ]

        self.fields['apply_remaining_to'].queryset = wallet_queryset
        self.fields['invoice'].empty_label = 'No unpaid invoice available' if not unpaid_invoice_queryset.exists() else 'Select Invoice (optional when paying multiple invoices)'
        self.fields['apply_remaining_to'].empty_label = 'No leftover balance available' if not wallet_queryset.exists() else 'Select the student wallet to apply'
        if self.instance and self.instance.pk:
            self.initial['invoices'] = [str(invoice_id) for invoice_id in (self.instance.invoices or [])]
            self.initial['invoice'] = self.instance.invoice_id

    @staticmethod
    def _get_student_wallet_balance(student):
        if student is None:
            return Decimal('0.00')
        return sum(
            Decimal(str(payment.remaining_balance or 0))
            for payment in student.payments.all()
            if Decimal(str(payment.remaining_balance or 0)) > Decimal('0.00')
        )

    def clean(self):
        cleaned_data = super().clean()
        primary_invoice = cleaned_data.get('invoice')
        selected_invoice_ids = [int(invoice_id) for invoice_id in cleaned_data.get('invoices') or [] if str(invoice_id).strip()]
        wallet_student = cleaned_data.get('apply_remaining_to')
        amount = cleaned_data.get('amount')
        payment_method = str(cleaned_data.get('payment_method') or '').strip().lower()

        if primary_invoice and primary_invoice.pk not in selected_invoice_ids and selected_invoice_ids:
            selected_invoice_ids.insert(0, primary_invoice.pk)

        if not primary_invoice and selected_invoice_ids:
            primary_invoice = StudentInvoice.objects.filter(pk=selected_invoice_ids[0]).first()
            cleaned_data['invoice'] = primary_invoice

        cleaned_data['invoices'] = list(dict.fromkeys(selected_invoice_ids))

        if not cleaned_data['invoice'] and not cleaned_data['invoices']:
            self.add_error('invoice', 'Select at least one invoice to apply the payment to.')
            self.add_error('invoices', 'Select at least one invoice to apply the payment to.')

        if cleaned_data.get('invoice') and not cleaned_data.get('invoices'):
            cleaned_data['invoices'] = [cleaned_data['invoice'].pk]

        if cleaned_data.get('invoices') and not cleaned_data.get('invoice'):
            cleaned_data['invoice'] = StudentInvoice.objects.filter(pk=cleaned_data['invoices'][0]).first()

        invoice_total = Decimal('0.00')
        for invoice_id in cleaned_data.get('invoices') or []:
            invoice = StudentInvoice.objects.filter(pk=invoice_id).first()
            if invoice:
                invoice_total += max(Decimal('0.00'), invoice.amount_due - invoice.total_paid)

        if wallet_student:
            wallet_balance = self._get_student_wallet_balance(wallet_student)
            if amount in (None, ''):
                amount = '0.00' if 'refund' in payment_method else str(invoice_total)
                cleaned_data['amount'] = amount
            try:
                amount_value = Decimal(str(amount))
            except Exception:
                amount_value = Decimal('0.00')

            if 'refund' in payment_method:
                if amount_value <= Decimal('0.00'):
                    self.add_error('amount', 'Enter the amount to return to the student.')
                if amount_value > wallet_balance:
                    self.add_error('apply_remaining_to', f"The selected wallet balance for {wallet_student.full_name} is insufficient for a refund. Available: ₦{wallet_balance:.2f}")
                cleaned_data['wallet_used'] = False
                cleaned_data['wallet_applied'] = Decimal('0.00')
                cleaned_data['wallet_refund_amount'] = amount_value
            else:
                if amount_value > wallet_balance:
                    self.add_error('apply_remaining_to', f"The selected wallet balance for {wallet_student.full_name} is insufficient. Available: ₦{wallet_balance:.2f}")
                cleaned_data['wallet_used'] = True
                cleaned_data['wallet_applied'] = min(wallet_balance, amount_value)
                cleaned_data['wallet_refund_amount'] = Decimal('0.00')
        else:
            if amount in (None, ''):
                self.add_error('amount', 'Enter the payment amount.')
            cleaned_data['wallet_used'] = False
            cleaned_data['wallet_applied'] = Decimal('0.00')
            cleaned_data['wallet_refund_amount'] = Decimal('0.00')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        selected_invoice_ids = list(dict.fromkeys(self.cleaned_data.get('invoices') or []))
        wallet_student = self.cleaned_data.get('apply_remaining_to')
        primary_invoice = self.cleaned_data.get('invoice')
        payment_method = str(self.cleaned_data.get('payment_method') or '').lower()
        instance.wallet_used = bool(wallet_student and 'refund' not in payment_method)
        instance.wallet_applied = Decimal(str(self.cleaned_data.get('wallet_applied') or 0))
        instance.wallet_refund_amount = Decimal(str(self.cleaned_data.get('wallet_refund_amount') or 0))

        if wallet_student and 'refund' not in payment_method:
            instance.student = wallet_student

        if not primary_invoice and selected_invoice_ids:
            primary_invoice = StudentInvoice.objects.filter(pk=selected_invoice_ids[0]).first()

        if 'refund' in payment_method and wallet_student:
            if instance.amount <= Decimal('0.00'):
                instance.amount = instance.wallet_refund_amount
            instance.student = wallet_student
            instance.invoice = primary_invoice or selected_invoice_ids and StudentInvoice.objects.filter(pk=selected_invoice_ids[0]).first()
            instance.invoices = [invoice.pk for invoice in ([instance.invoice] if instance.invoice else [])]
            instance.allocations = []
            instance.remaining_balance = Decimal('0.00')
            instance.wallet_used = False
            instance.wallet_applied = Decimal('0.00')

        elif selected_invoice_ids:
            instance.remaining_balance = Decimal('0.00')
            invoice_map = {
                invoice.pk: invoice for invoice in StudentInvoice.objects.filter(pk__in=selected_invoice_ids)
                .select_related('student', 'fee')
            }
            selected_invoices = [invoice_map[invoice_id] for invoice_id in selected_invoice_ids if invoice_id in invoice_map]
            if primary_invoice and primary_invoice.pk not in selected_invoice_ids:
                selected_invoices.insert(0, primary_invoice)
            selected_invoices = list({invoice.pk: invoice for invoice in selected_invoices}.values())

            grouped_invoices = {}
            for invoice in selected_invoices:
                grouped_invoices.setdefault(invoice.student_id, []).append(invoice)

            if len(grouped_invoices) > 1:
                unallocated_payment = Decimal(str(self.cleaned_data.get('amount')))
                created_payments = []
                for student_id, student_invoices in grouped_invoices.items():
                    group_outstanding = sum(
                        max(Decimal('0.00'), invoice.amount_due - invoice.total_paid)
                        for invoice in student_invoices
                    )
                    if group_outstanding <= Decimal('0.00'):
                        continue

                    amount_for_student = min(unallocated_payment, group_outstanding)
                    if amount_for_student <= Decimal('0.00'):
                        continue

                    payment_invoices = []
                    payment_allocations = []
                    student_total = Decimal('0.00')
                    remaining_for_student = amount_for_student

                    for invoice in student_invoices:
                        outstanding = max(Decimal('0.00'), invoice.amount_due - invoice.total_paid)
                        if outstanding <= Decimal('0.00'):
                            continue

                        amount_applied = min(remaining_for_student, outstanding)
                        payment_invoices.append(invoice.pk)
                        payment_allocations.append({
                            'invoice_id': invoice.pk,
                            'amount_applied': str(amount_applied),
                            'remaining_balance': str(max(Decimal('0.00'), outstanding - amount_applied)),
                        })
                        student_total += amount_applied
                        remaining_for_student -= amount_applied
                        if remaining_for_student <= Decimal('0.00'):
                            break

                    if not payment_invoices:
                        continue

                    payment = StudentPayment(
                        student_id=student_id,
                        invoice_id=student_invoices[0].pk,
                        amount=student_total,
                        payment_date=self.cleaned_data.get('payment_date'),
                        payment_method=self.cleaned_data.get('payment_method', ''),
                        reference=self.cleaned_data.get('reference', ''),
                        notes=self.cleaned_data.get('notes', ''),
                        invoices=payment_invoices,
                        allocations=payment_allocations,
                        remaining_balance=Decimal('0.00'),
                    )
                    if commit:
                        payment.save()
                    created_payments.append(payment)
                    unallocated_payment = max(Decimal('0.00'), unallocated_payment - amount_for_student)

                if created_payments:
                    return created_payments[0]

            instance.invoice = selected_invoices[0]
            if not wallet_student or 'refund' in payment_method:
                instance.student = selected_invoices[0].student
            instance.invoices = [invoice.pk for invoice in selected_invoices]
            instance.allocations = []
            remaining_payment = instance.amount
            for invoice in selected_invoices:
                available_balance = max(Decimal('0.00'), invoice.amount_due - invoice.total_paid)
                amount_applied = min(remaining_payment, available_balance)
                instance.allocations.append({
                    'invoice_id': invoice.pk,
                    'amount_applied': str(amount_applied),
                    'remaining_balance': str(max(Decimal('0.00'), available_balance - amount_applied)),
                })
                remaining_payment -= amount_applied
            instance.remaining_balance = max(Decimal('0.00'), remaining_payment)
        elif primary_invoice:
            instance.invoice = primary_invoice
            if not wallet_student or 'refund' in payment_method:
                instance.student = primary_invoice.student
            instance.invoices = [primary_invoice.pk]
            instance.allocations = [{
                'invoice_id': primary_invoice.pk,
                'amount_applied': str(instance.amount),
                'remaining_balance': '0.00',
            }]
            instance.remaining_balance = Decimal('0.00')
        else:
            instance.invoices = []
            instance.allocations = []
            instance.remaining_balance = Decimal('0.00')

        if commit:
            instance.save()

        if wallet_student and 'refund' not in payment_method and instance.wallet_applied > Decimal('0.00'):
            instance.remaining_balance = Decimal('0.00')
            StudentPayment.consume_student_wallet(wallet_student, instance.wallet_applied)
        elif wallet_student and 'refund' in payment_method and instance.wallet_refund_amount > Decimal('0.00'):
            instance.remaining_balance = Decimal('0.00')
            StudentPayment.refund_student_wallet(wallet_student, instance.wallet_refund_amount)

        if commit:
            instance.refresh_from_db()
        return instance
