from django import forms

from .models import SchoolExpense, SchoolFee, StudentInvoice, StudentPayment


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
        fields = ['name', 'amount', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class StudentInvoiceForm(forms.ModelForm):
    class Meta:
        model = StudentInvoice
        fields = ['student', 'fee', 'issued_date', 'due_date', 'amount_due', 'status', 'notes']
        widgets = {
            'issued_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class InvoiceChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        student_label = obj.student if obj.student else 'Unknown student'
        amount_label = f"₦{obj.amount_due}"
        fee_label = f" ({obj.fee})" if obj.fee else ''
        return f"Invoice {obj.id} - {student_label}{fee_label} - {amount_label}"


class StudentPaymentForm(forms.ModelForm):
    invoice = InvoiceChoiceField(
        queryset=StudentInvoice.objects.select_related('student', 'fee').order_by('-issued_date'),
        empty_label='Select Invoice'
    )

    class Meta:
        model = StudentPayment
        fields = ['invoice', 'amount', 'payment_date', 'payment_method', 'reference', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.invoice:
            instance.student = instance.invoice.student
        if commit:
            instance.save()
        return instance
