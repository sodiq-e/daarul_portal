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
