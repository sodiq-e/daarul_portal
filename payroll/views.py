from django.contrib import messages
from django.db.models import Sum
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import SchoolExpense, SchoolFee, StudentInvoice, StudentPayment
from .forms import SchoolExpenseForm, SchoolFeeForm, StudentInvoiceForm, StudentPaymentForm


def staff_can_manage(user):
    return (
        getattr(user, 'profile', None) is not None and
        user.profile.is_approved and
        user.groups.filter(name__in=['Teacher', 'Staff']).exists()
    )


class PayrollDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'payroll/dashboard.html'

    def test_func(self):
        return staff_can_manage(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expenses = SchoolExpense.objects.all()
        invoices = StudentInvoice.objects.select_related('student', 'fee').all()
        payments = StudentPayment.objects.select_related('student', 'invoice').all()
        context['total_expenses'] = expenses.aggregate(total=Sum('amount'))['total'] or 0
        context['total_invoiced'] = invoices.aggregate(total=Sum('amount_due'))['total'] or 0
        context['total_collected'] = payments.aggregate(total=Sum('amount'))['total'] or 0
        context['outstanding_balance'] = sum(inv.balance for inv in invoices)
        context['owing_invoices'] = invoices.filter(amount_due__gt=0)
        context['recent_expenses'] = expenses.order_by('-date')[:10]
        context['recent_invoices'] = invoices.order_by('-issued_date')[:10]
        context['recent_payments'] = payments.order_by('-payment_date')[:10]
        return context


class SchoolExpenseListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = SchoolExpense
    template_name = 'payroll/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 20

    def test_func(self):
        return staff_can_manage(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_expenses'] = self.get_queryset().aggregate(total=Sum('amount'))['total'] or 0
        return context


class SchoolExpenseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = SchoolExpense
    form_class = SchoolExpenseForm
    template_name = 'payroll/expense_form.html'
    success_url = reverse_lazy('expense_list')

    def test_func(self):
        return staff_can_manage(self.request.user)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'School expense recorded successfully.')
        return super().form_valid(form)


class SchoolFeeListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = SchoolFee
    template_name = 'payroll/fee_list.html'
    context_object_name = 'fees'

    def test_func(self):
        return staff_can_manage(self.request.user)


class SchoolFeeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = SchoolFee
    form_class = SchoolFeeForm
    template_name = 'payroll/fee_form.html'
    success_url = reverse_lazy('fee_list')

    def test_func(self):
        return staff_can_manage(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'School fee type saved successfully.')
        return super().form_valid(form)


class StudentInvoiceListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = StudentInvoice
    template_name = 'payroll/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20

    def test_func(self):
        return staff_can_manage(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoices = self.get_queryset()
        context['total_due'] = invoices.aggregate(total=Sum('amount_due'))['total'] or 0
        context['total_paid'] = sum(inv.total_paid for inv in invoices)
        context['total_balance'] = sum(inv.balance for inv in invoices)
        context['owing_count'] = sum(1 for inv in invoices if inv.is_owing)
        return context


class StudentInvoiceDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = StudentInvoice
    template_name = 'payroll/invoice_detail.html'
    context_object_name = 'invoice'

    def test_func(self):
        return staff_can_manage(self.request.user)


class StudentInvoiceCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = StudentInvoice
    form_class = StudentInvoiceForm
    template_name = 'payroll/invoice_form.html'
    success_url = reverse_lazy('invoice_list')

    def test_func(self):
        return staff_can_manage(self.request.user)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Student invoice created successfully.')
        return super().form_valid(form)


class StudentPaymentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = StudentPayment
    form_class = StudentPaymentForm
    template_name = 'payroll/payment_form.html'
    success_url = reverse_lazy('invoice_list')

    def test_func(self):
        return staff_can_manage(self.request.user)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Payment recorded successfully.')
        return super().form_valid(form)


class StudentPaymentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = StudentPayment
    template_name = 'payroll/payment_detail.html'
    context_object_name = 'payment'

    def test_func(self):
        return staff_can_manage(self.request.user)


class StudentPaymentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = StudentPayment
    template_name = 'payroll/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20

    def test_func(self):
        return staff_can_manage(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payments = self.get_queryset()
        context['total_payments'] = payments.aggregate(total=Sum('amount'))['total'] or 0
        return context
