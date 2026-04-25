from django.contrib import messages
from django.db.models import Sum
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from .models import SchoolExpense, SchoolFee, StudentInvoice, StudentPayment, Staff, Payslip, SalaryComponent, PayrollDashboard
from .forms import SchoolExpenseForm, SchoolFeeForm, StudentInvoiceForm, StudentPaymentForm


def staff_can_manage(user):
    """Check if user can manage payroll (approve staff access)"""
    if not user or not user.is_authenticated:
        return False
    
    try:
        return (
            getattr(user, 'profile', None) is not None and
            user.profile.is_approved and
            user.groups.filter(name__in=['Teacher', 'Staff']).exists()
        )
    except AttributeError:
        # Profile doesn't exist or other attribute error
        return False
    except Exception as e:
        # Log unexpected errors but don't crash
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in staff_can_manage: {str(e)}")
        return False


def teacher_has_permission(teacher, permission_code):
    """Check if teacher has specific permission"""
    from school_classes.models import TeacherPermission
    try:
        perm = TeacherPermission.objects.filter(
            teacher=teacher,
            permission=permission_code,
            is_granted=True
        ).exists()
        return perm
    except:
        return False


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


class SchoolFeeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SchoolFee
    form_class = SchoolFeeForm
    template_name = 'payroll/fee_form.html'
    success_url = reverse_lazy('fee_list')

    def test_func(self):
        return staff_can_manage(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'School fee type updated successfully.')
        return super().form_valid(form)


class SchoolFeeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = SchoolFee
    template_name = 'payroll/fee_confirm_delete.html'
    success_url = reverse_lazy('fee_list')

    def test_func(self):
        return staff_can_manage(self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'School fee type deleted successfully.')
        return super().delete(request, *args, **kwargs)


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


# ==================== TEACHER PAYROLL VIEWS ====================

@method_decorator(login_required, name='dispatch')
class TeacherPayrollView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Teacher views their own payroll information"""
    template_name = 'teachers/payroll/teacher_payroll.html'

    def test_func(self):
        try:
            teacher = self.request.user.teacher_profile
            return teacher_has_permission(teacher, 'view_payroll')
        except:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.request.user.teacher_profile

        # Get staff record linked to this teacher
        try:
            staff = Staff.objects.get(teacher=teacher)
            context['staff'] = staff
            context['basic_salary'] = staff.basic

            # Get salary components
            salary_components = SalaryComponent.objects.filter(
                staff=staff,
                is_active=True
            )
            context['salary_components'] = salary_components

            # Calculate totals
            allowances = salary_components.filter(
                component_type__in=['allowance', 'bonus']
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            deductions = salary_components.filter(
                component_type='deduction'
            ).aggregate(total=Sum('amount'))['total'] or 0

            context['total_allowances'] = allowances
            context['total_deductions'] = deductions
            context['gross_salary'] = staff.basic + allowances
            context['net_salary'] = context['gross_salary'] - deductions

        except Staff.DoesNotExist:
            context['staff'] = None
            messages.warning(
                self.request,
                'Your payroll profile has not been set up yet. Please contact administration.'
            )

        return context


@method_decorator(login_required, name='dispatch')
class TeacherPayrollDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Teacher views their payroll dashboard with monthly details"""
    template_name = 'teachers/payroll/payroll_dashboard.html'

    def test_func(self):
        try:
            teacher = self.request.user.teacher_profile
            return teacher_has_permission(teacher, 'view_payroll_dashboard')
        except:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.request.user.teacher_profile

        try:
            staff = Staff.objects.get(teacher=teacher)
            context['staff'] = staff

            # Get last 12 months of payslips
            today = datetime.now().date()
            start_date = today - relativedelta(months=12)

            payslips = Payslip.objects.filter(
                staff=staff,
                month__gte=start_date
            ).order_by('-month')

            context['payslips'] = payslips

            # Calculate summary stats
            if payslips.exists():
                total_gross = payslips.aggregate(total=Sum('gross'))['total'] or 0
                total_deductions = payslips.aggregate(total=Sum('total_deductions'))['total'] or 0
                total_net = payslips.aggregate(total=Sum('net'))['total'] or 0
                avg_monthly_net = total_net / payslips.count() if payslips.count() > 0 else 0

                context['summary'] = {
                    'total_gross': total_gross,
                    'total_deductions': total_deductions,
                    'total_net': total_net,
                    'avg_monthly_net': avg_monthly_net,
                    'payslip_count': payslips.count()
                }

        except Staff.DoesNotExist:
            context['staff'] = None
            messages.warning(
                self.request,
                'Your payroll profile has not been set up yet. Please contact administration.'
            )

        return context


@method_decorator(login_required, name='dispatch')
class TeacherPayslipDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Teacher views a specific payslip"""
    model = Payslip
    template_name = 'teachers/payroll/payslip_detail.html'
    context_object_name = 'payslip'

    def test_func(self):
        try:
            teacher = self.request.user.teacher_profile
            payslip = self.get_object()
            # Verify teacher owns this payslip
            return payslip.staff.teacher == teacher and teacher_has_permission(teacher, 'view_payroll')
        except:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payslip = self.get_object()

        # Get salary components active for this payslip month
        salary_components = SalaryComponent.objects.filter(
            staff=payslip.staff,
            is_active=True,
            effective_date__lte=payslip.month
        )

        context['allowances'] = salary_components.filter(
            component_type__in=['allowance', 'bonus']
        )
        context['deductions'] = salary_components.filter(
            component_type='deduction'
        )

        return context


@login_required
def teacher_print_payslip(request, pk):
    """Print payslip for teacher"""
    payslip = get_object_or_404(Payslip, pk=pk)

    try:
        teacher = request.user.teacher_profile
        if payslip.staff.teacher != teacher:
            messages.error(request, 'You are not authorized to view this payslip.')
            return redirect('home')
        
        if not teacher_has_permission(teacher, 'view_payroll'):
            messages.error(request, 'You do not have permission to view payroll.')
            return redirect('home')

    except:
        messages.error(request, 'You must be a teacher to access this page.')
        return redirect('home')

    # Get salary components
    salary_components = SalaryComponent.objects.filter(
        staff=payslip.staff,
        is_active=True,
        effective_date__lte=payslip.month
    )

    context = {
        'payslip': payslip,
        'allowances': salary_components.filter(component_type__in=['allowance', 'bonus']),
        'deductions': salary_components.filter(component_type='deduction'),
    }

    from django.template.loader import render_to_string
    from django.http import HttpResponse

    html = render_to_string('teachers/payroll/payslip_print.html', context)
    
    response = HttpResponse(html)
    response['Content-Type'] = 'text/html'
    return response

