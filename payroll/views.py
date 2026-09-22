from django.contrib import messages
from django.db.models import Sum
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from .models import SchoolExpense, SchoolFee, StudentInvoice, StudentPayment, Staff, Payslip, SalaryComponent, PayrollDashboard
from exams.models import Term
from students.models import Student
from .forms import SchoolExpenseForm, SchoolFeeForm, StudentInvoiceForm, StudentPaymentForm
from settingsapp.tenant_utils import get_request_tenant, user_is_tenant_staff


def staff_can_manage(user, request=None):
    """Check if user can manage payroll (approve staff access)"""
    if not user or not user.is_authenticated:
        return False

    try:
        tenant = get_request_tenant(request) if request is not None else None
        if tenant is None:
            return (
                getattr(user, 'profile', None) is not None and
                user.profile.is_approved and
                user.groups.filter(name__in=['Teacher', 'Staff']).exists()
            )
        return getattr(user, 'profile', None) is not None and user.profile.is_approved and user_is_tenant_staff(user, tenant=tenant)
    except AttributeError:
        return False
    except Exception as e:
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

    def get_queryset(self):
        qs = super().get_queryset().select_related('student', 'fee', 'term')
        academic_session = self.request.GET.get('academic_session')
        term_id = self.request.GET.get('term')
        student_id = self.request.GET.get('student')

        if academic_session:
            qs = qs.filter(academic_session=academic_session)

        if term_id:
            try:
                qs = qs.filter(term__id=int(term_id))
            except ValueError:
                pass

        if student_id:
            try:
                qs = qs.filter(student__id=int(student_id))
            except ValueError:
                pass

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoices = self.get_queryset()
        context['total_due'] = invoices.aggregate(total=Sum('amount_due'))['total'] or 0
        context['total_paid'] = sum(inv.total_paid for inv in invoices)
        context['total_balance'] = sum(inv.balance for inv in invoices)
        context['owing_count'] = sum(1 for inv in invoices if inv.is_owing)
        context['academic_sessions'] = Term.objects.order_by('academic_year').values_list('academic_year', flat=True).distinct()
        context['terms'] = Term.objects.order_by('academic_year', 'name')
        context['students'] = Student.objects.order_by('surname', 'other_names')
        context['selected_academic_session'] = self.request.GET.get('academic_session', '')
        context['selected_term'] = self.request.GET.get('term', '')
        context['selected_student'] = self.request.GET.get('student', '')
        return context


@login_required
def print_invoices(request):
    """Print invoices filtered by students, academic session, and/or term.

    GET parameters:
    - students: comma-separated student IDs (optional)
    - academic_session: string (optional)
    - term: term id (optional)
    - all: if present and true, ignore student selection and print all
    """
    if not staff_can_manage(request.user):
        from django.shortcuts import redirect
        from django.contrib import messages
        messages.error(request, 'You do not have permission to print invoices.')
        return redirect('invoice_list')

    qs = StudentInvoice.objects.select_related('student', 'term').all()

    raw_student_values = request.GET.getlist('students') + request.GET.getlist('student')
    student_ids = []
    for value in raw_student_values:
        if not value:
            continue
        for item in value.split(','):
            item = item.strip()
            if not item:
                continue
            try:
                student_ids.append(int(item))
            except ValueError:
                pass

    academic_session = request.GET.get('academic_session')
    term_param = request.GET.get('term')
    all_flag = request.GET.get('all')

    if student_ids and not all_flag:
        qs = qs.filter(student__id__in=sorted(set(student_ids)))

    if academic_session:
        qs = qs.filter(academic_session=academic_session)

    if term_param:
        try:
            term_id = int(term_param)
            qs = qs.filter(term__id=term_id)
        except ValueError:
            pass

    invoices = qs.order_by('student__surname', 'issued_date')
    total_due = invoices.aggregate(total=Sum('amount_due'))['total'] or 0
    total_paid = sum(inv.total_paid for inv in invoices)
    total_balance = sum(inv.balance for inv in invoices)

    selected_student_ids = sorted(set(student_ids))
    return render(request, 'payroll/print_invoices.html', {
        'invoices': invoices,
        'total_due': total_due,
        'total_paid': total_paid,
        'total_balance': total_balance,
        'academic_sessions': Term.objects.order_by('academic_year').values_list('academic_year', flat=True).distinct(),
        'terms': Term.objects.order_by('academic_year', 'name'),
        'students': Student.objects.order_by('surname', 'other_names'),
        'selected_academic_session': academic_session or '',
        'selected_term': term_param or '',
        'selected_students': selected_student_ids,
        'selected_student': ','.join(str(student_id) for student_id in selected_student_ids),
        'current_type': 'invoices',
    })


@login_required
def print_receipts(request):
    """Print student receipts filtered by students, academic session, and/or term.

    GET parameters same as print_invoices but operates on StudentPayment.
    """
    if not staff_can_manage(request.user):
        from django.shortcuts import redirect
        from django.contrib import messages
        messages.error(request, 'You do not have permission to print receipts.')
        return redirect('payment_list')

    qs = StudentPayment.objects.select_related('student', 'invoice').all()

    raw_student_values = request.GET.getlist('students') + request.GET.getlist('student')
    student_ids = []
    for value in raw_student_values:
        if not value:
            continue
        for item in value.split(','):
            item = item.strip()
            if not item:
                continue
            try:
                student_ids.append(int(item))
            except ValueError:
                pass

    academic_session = request.GET.get('academic_session')
    term_param = request.GET.get('term')
    all_flag = request.GET.get('all')

    if student_ids and not all_flag:
        qs = qs.filter(student__id__in=sorted(set(student_ids)))

    if academic_session:
        qs = qs.filter(invoice__academic_session=academic_session)

    if term_param:
        try:
            term_id = int(term_param)
            qs = qs.filter(invoice__term__id=term_id)
        except ValueError:
            pass

    receipts = list(qs.order_by('student__surname', 'payment_date'))

    invoice_qs = StudentInvoice.objects.select_related('student', 'fee').all()
    if student_ids and not all_flag:
        invoice_qs = invoice_qs.filter(student__id__in=sorted(set(student_ids)))
    if academic_session:
        invoice_qs = invoice_qs.filter(academic_session=academic_session)
    if term_param:
        try:
            term_id = int(term_param)
            invoice_qs = invoice_qs.filter(term__id=term_id)
        except ValueError:
            pass

    invoice_lookup = {invoice.pk: invoice for invoice in invoice_qs}
    for receipt in receipts:
        invoice_names = []
        invoice_allocations = []
        for allocation in receipt.allocations or []:
            invoice_id = allocation.get('invoice_id')
            if invoice_id is None:
                continue
            try:
                invoice_pk = int(invoice_id)
            except (TypeError, ValueError):
                continue
            invoice = invoice_lookup.get(invoice_pk)
            if invoice and invoice.fee:
                invoice_name = invoice.fee.name
            else:
                invoice_name = f'Invoice #{invoice_pk}'
            invoice_names.append(invoice_name)
            invoice_allocations.append({
                'invoice_name': invoice_name,
                'amount_applied': allocation.get('amount_applied', receipt.amount),
            })

        if not invoice_allocations and getattr(receipt, 'invoice', None):
            invoice = receipt.invoice
            invoice_name = invoice.fee.name if invoice and invoice.fee else f'Invoice #{invoice.pk}'
            invoice_names.append(invoice_name)
            invoice_allocations.append({
                'invoice_name': invoice_name,
                'amount_applied': receipt.amount,
            })

        receipt.invoice_names = invoice_names
        receipt.invoice_allocations = invoice_allocations

    total_due = invoice_qs.aggregate(total=Sum('amount_due'))['total'] or 0
    total_paid = sum(receipt.amount for receipt in receipts)
    total_balance = sum(inv.balance for inv in invoice_qs)
    selected_student_ids = sorted(set(student_ids))

    return render(request, 'payroll/print_receipts.html', {
        'receipts': receipts,
        'total_due': total_due,
        'total_paid': total_paid,
        'total_balance': total_balance,
        'academic_sessions': Term.objects.order_by('academic_year').values_list('academic_year', flat=True).distinct(),
        'terms': Term.objects.order_by('academic_year', 'name'),
        'students': Student.objects.order_by('surname', 'other_names'),
        'selected_academic_session': academic_session or '',
        'selected_term': term_param or '',
        'selected_students': selected_student_ids,
        'selected_student': ','.join(str(student_id) for student_id in selected_student_ids),
        'current_type': 'receipts',
    })


@login_required
def student_fee_options(request):
    if not staff_can_manage(request.user):
        return JsonResponse({'fees': []}, status=403)

    student_id = request.GET.get('student')
    if not student_id:
        return JsonResponse({'fees': []})

    try:
        student = Student.objects.select_related('student_class').get(pk=student_id)
    except (Student.DoesNotExist, ValueError):
        return JsonResponse({'fees': []})

    inherited_fee_ids = set(
        SchoolFee.objects.filter(school_classes=student.student_class).values_list('id', flat=True)
    )
    fees = SchoolFee.objects.order_by('name')
    return JsonResponse({
        'fees': [
            {
                'id': fee.id,
                'name': fee.name,
                'amount': str(fee.amount),
                'selected': fee.id in inherited_fee_ids,
            }
            for fee in fees
        ]
    })


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
        invoice_data = form.cleaned_data
        active_tenant = get_request_tenant(self.request)
        invoices = [StudentInvoice(
            student=invoice_data['student'],
            fee=fee,
            issued_date=invoice_data['issued_date'],
            due_date=invoice_data['due_date'],
            amount_due=fee.amount,
            academic_session=invoice_data['academic_session'],
            term=invoice_data['term'],
            status=invoice_data['status'],
            notes=invoice_data['notes'],
            created_by=self.request.user,
            tenant=active_tenant,
        ) for fee in invoice_data['fees']]

        for invoice in invoices:
            invoice.status = 'overdue' if invoice.due_date < datetime.today().date() else 'pending'

        StudentInvoice.objects.bulk_create(invoices)
        messages.success(self.request, f'{len(invoices)} student invoice(s) created successfully.')
        return redirect(self.success_url)


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

    def get_queryset(self):
        qs = super().get_queryset().select_related('student', 'invoice', 'invoice__term')
        academic_session = self.request.GET.get('academic_session')
        term_id = self.request.GET.get('term')
        student_id = self.request.GET.get('student')

        if academic_session:
            qs = qs.filter(invoice__academic_session=academic_session)

        if term_id:
            try:
                qs = qs.filter(invoice__term__id=int(term_id))
            except ValueError:
                pass

        if student_id:
            try:
                qs = qs.filter(student__id=int(student_id))
            except ValueError:
                pass

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payments = self.get_queryset()
        context['total_payments'] = payments.aggregate(total=Sum('amount'))['total'] or 0
        context['academic_sessions'] = Term.objects.order_by('academic_year').values_list('academic_year', flat=True).distinct()
        context['terms'] = Term.objects.order_by('academic_year', 'name').all()
        context['students'] = Student.objects.order_by('surname', 'other_names').all()
        context['selected_academic_session'] = self.request.GET.get('academic_session', '')
        context['selected_term'] = self.request.GET.get('term', '')
        context['selected_student'] = self.request.GET.get('student', '')
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

