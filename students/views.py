from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q, Avg, Count, Sum, Max, Min
from exams.models import Term

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from .models import Student, StudentApplication, AdmissionFormField, AdmissionFormResponse
from .forms import StudentForm, StudentApplicationForm, StudentApplicationReviewForm, DynamicAdmissionForm
from school_classes.models import ClassTeacher


def user_profile_approved(user):
    """Defensively check if user profile is approved"""
    try:
        return user.profile.is_approved
    except AttributeError:
        return False


def staff_can_edit(user):
    """Check if user can edit student records"""
    if not user or not user.is_authenticated:
        return False
    
    try:
        return (
            getattr(user, 'profile', None) is not None and
            user.profile.is_approved and
            user.groups.filter(name__in=['Teacher', 'Staff']).exists()
        )
    except AttributeError:
        return False
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in staff_can_edit: {str(e)}")
        return False


class StudentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 20

    def test_func(self):
        return user_profile_approved(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = staff_can_edit(self.request.user)
        return context


class StudentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'

    def test_func(self):
        return user_profile_approved(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = staff_can_edit(self.request.user)
        
        # Check if user is class teacher for this student
        student = self.get_object()
        is_class_teacher = False
        if hasattr(self.request.user, 'teacher_profile') and student.student_class:
            is_class_teacher = ClassTeacher.objects.filter(
                teacher=self.request.user.teacher_profile,
                school_class=student.student_class,
                is_class_teacher=True,
                is_active=True
            ).exists()
        
        context['is_class_teacher'] = is_class_teacher
        return context


class StudentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student_list')

    def test_func(self):
        return staff_can_edit(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Student created successfully.')
        return super().form_valid(form)


class StudentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student_list')

    def test_func(self):
        return staff_can_edit(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Student updated successfully.')
        return super().form_valid(form)


class StudentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Student
    template_name = 'students/student_confirm_delete.html'
    success_url = reverse_lazy('student_list')

    def test_func(self):
        return staff_can_edit(self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Student deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
def student_status_update(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        date_left = request.POST.get('date_left')
        if status in ['transferred', 'graduated']:
            student.status = status
            if date_left:
                student.date_left = date_left
            student.save()
            messages.success(request, f'Student status updated to {status}.')
            return redirect('student_detail', pk=pk)
    return render(request, 'students/student_status_update.html', {'student': student})


class StudentApplicationCreateView(CreateView):
    model = StudentApplication
    form_class = StudentApplicationForm
    template_name = 'students/student_application_modern.html'
    success_url = reverse_lazy('student_application')

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.submitted_by = self.request.user
        messages.success(self.request, '✓ Your application has been submitted successfully. The school will review it shortly.')
        return super().form_valid(form)


class StudentApplicationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = StudentApplication
    template_name = 'students/student_application_list.html'
    context_object_name = 'applications'
    paginate_by = 20

    def test_func(self):
        return staff_can_edit(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = self.get_queryset().filter(status='pending').count()
        context['accepted_count'] = self.get_queryset().filter(status='accepted').count()
        context['rejected_count'] = self.get_queryset().filter(status='rejected').count()
        return context


class StudentApplicationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = StudentApplication
    template_name = 'students/student_application_detail.html'
    context_object_name = 'application'

    def test_func(self):
        return staff_can_edit(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_responses'] = AdmissionFormResponse.objects.filter(
            application=self.object
        ).select_related('field')
        return context


@login_required
def print_admission_application(request, pk):
    """Print admission application in PDF format"""
    if not request.user.is_staff:
        return redirect('home')
    
    application = get_object_or_404(StudentApplication, pk=pk)
    form_responses = AdmissionFormResponse.objects.filter(application=application).select_related('field')
    
    context = {
        'application': application,
        'form_responses': form_responses,
    }
    
    html_string = render_to_string('students/admission_application_print.html', context)
    
    # Try to generate PDF, fallback to HTML if weasyprint not available
    try:
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Application_{application.id}.pdf"'
        return response
    except:
        # Fallback: return HTML for printing
        return HttpResponse(html_string)


class StudentApplicationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = StudentApplication
    form_class = StudentApplicationReviewForm
    template_name = 'students/student_application_form.html'
    success_url = reverse_lazy('student_application_list')

    def test_func(self):
        return staff_can_edit(self.request.user)

    def form_valid(self, form):
        form.instance.reviewed_by = self.request.user
        messages.success(self.request, 'Application updated successfully.')
        return super().form_valid(form)


# ==================== STUDENT PORTAL VIEWS ====================

class StudentDashboardView(LoginRequiredMixin, TemplateView):
    """Student view their own profile and summary"""
    template_name = 'students/portal/student_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            student = self.request.user.student_profile
            context['student'] = student
            context['invoices'] = student.invoices.all().order_by('-issued_date')
            context['pending_invoices'] = student.invoices.filter(status='pending').count()
            context['total_owing'] = sum(inv.balance for inv in student.invoices.filter(status__in=['pending', 'overdue']))
            try:
                from cbt.models import CBTExam, CBTStudentAttempt
                now = timezone.now()
                student_class = getattr(student, 'student_class', None)
                context['active_attempts'] = CBTStudentAttempt.objects.filter(
                    student=self.request.user,
                    is_submitted=False
                ).select_related('exam').order_by('-started_at')
                context['recent_cbt_results'] = CBTStudentAttempt.objects.filter(
                    student=self.request.user,
                    is_submitted=True
                ).select_related('exam').order_by('-completed_at')[:5]
                if student_class:
                    context['upcoming_cbt_exams'] = CBTExam.objects.filter(
                        exam_mode=CBTExam.REAL,
                        is_active=True,
                        is_published=True,
                        start_datetime__gt=now,
                        school_class=student_class
                    ).order_by('start_datetime')
                else:
                    context['upcoming_cbt_exams'] = CBTExam.objects.none()
            except Exception:
                context['active_attempts'] = []
                context['recent_cbt_results'] = []
                context['upcoming_cbt_exams'] = []
        except Student.DoesNotExist:
            context['student'] = None
        return context
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'student_profile'):
            messages.error(request, 'You do not have a student profile linked to your account.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class StudentProfileDetailView(LoginRequiredMixin, DetailView):
    """Student view their full profile"""
    model = Student
    template_name = 'students/portal/student_profile.html'
    context_object_name = 'student'
    
    def get_object(self):
        return self.request.user.student_profile
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'student_profile'):
            messages.error(request, 'You do not have a student profile.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class StudentResultsView(LoginRequiredMixin, TemplateView):
    """Student view their academic results"""
    template_name = 'students/portal/student_results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from results.models import StudentResult
            student = self.request.user.student_profile
            academic_session = self.request.GET.get('academic_session', '').strip()
            term_id = self.request.GET.get('term', '').strip()

            context['student'] = student
            context['selected_academic_session'] = academic_session
            context['selected_term'] = term_id

            # Base query for published results
            results_qs = StudentResult.objects.filter(
                student=student,
                is_published=True
            )

            if academic_session:
                results_qs = results_qs.filter(term__academic_year=academic_session)
            if term_id:
                results_qs = results_qs.filter(term_id=term_id)

            results = results_qs.select_related(
                'class_subject__subject',
                'term',
                'result_template'
            ).order_by('-term__academic_year', '-term__name')

            context['results'] = results
            context['academic_sessions'] = StudentResult.objects.filter(
                student=student,
                is_published=True
            ).order_by('term__academic_year').values_list('term__academic_year', flat=True).distinct()
            term_qs = Term.objects.filter(
                studentresult__student=student,
                studentresult__is_published=True
            ).distinct().order_by('academic_year', 'name')
            if academic_session:
                term_qs = term_qs.filter(academic_year=academic_session)

            context['terms'] = term_qs

            # Performance summary for the filtered results
            published_results = results.filter(percentage__isnull=False)
            average_percentage = published_results.aggregate(avg=Avg('percentage'))['avg'] or 0
            result_count = published_results.count()

            performance_by_term = published_results.values(
                'term__id',
                'term__display_name',
                'term__academic_year'
            ).annotate(
                avg_percentage=Avg('percentage'),
                total_score=Sum('total_score')
            ).order_by('term__academic_year', 'term__name')

            top_subjects = published_results.values(
                'class_subject__subject__name'
            ).annotate(
                avg_percentage=Avg('percentage')
            ).order_by('-avg_percentage')[:5]

            context['performance_summary'] = {
                'result_count': result_count,
                'average_percentage': round(float(average_percentage), 2) if average_percentage else 0,
                'highest_percentage': published_results.aggregate(max_percent=Max('percentage'))['max_percent'] or 0,
                'lowest_percentage': published_results.aggregate(min_percent=Min('percentage'))['min_percent'] or 0,
            }
            context['performance_by_term'] = list(performance_by_term)
            context['top_subjects'] = list(top_subjects)
            context['chart_labels'] = [
                f"{item['term__display_name']} {item['term__academic_year']}"
                for item in performance_by_term
            ]
            context['chart_data'] = [
                round(float(item['avg_percentage'] or 0), 2)
                for item in performance_by_term
            ]

        except Student.DoesNotExist:
            context['student'] = None
            context['results'] = []
            context['academic_sessions'] = []
            context['terms'] = []
            context['selected_academic_session'] = ''
            context['selected_term'] = ''
            context['performance_summary'] = {}
            context['performance_by_term'] = []
            context['top_subjects'] = []
            context['chart_labels'] = []
            context['chart_data'] = []
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in StudentResultsView: {str(e)}")
            context['student'] = None
            context['results'] = []
            context['academic_sessions'] = []
            context['terms'] = []
            context['selected_academic_session'] = ''
            context['selected_term'] = ''
            context['performance_summary'] = {}
            context['performance_by_term'] = []
            context['top_subjects'] = []
            context['chart_labels'] = []
            context['chart_data'] = []
        return context


class StudentFeesView(LoginRequiredMixin, TemplateView):
    """Student view their fee/invoice records"""
    template_name = 'students/portal/student_fees.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from payroll.models import StudentPayment
            student = self.request.user.student_profile
            academic_session = self.request.GET.get('academic_session', '').strip()
            term_id = self.request.GET.get('term', '').strip()

            invoices = student.invoices.all().order_by('-issued_date')
            if academic_session:
                invoices = invoices.filter(academic_session=academic_session)
            if term_id:
                invoices = invoices.filter(term_id=term_id)

            payments = StudentPayment.objects.filter(invoice__in=invoices).order_by('-payment_date')

            context['student'] = student
            context['invoices'] = invoices
            context['payments'] = payments
            context['academic_sessions'] = student.invoices.order_by('academic_session').values_list('academic_session', flat=True).distinct()
            context['terms'] = Term.objects.filter(invoices__student=student).distinct().order_by('academic_year', 'name')
            context['selected_academic_session'] = academic_session
            context['selected_term'] = term_id

            # Summary calculations
            total_due = sum(inv.amount_due for inv in invoices)
            total_paid = sum(p.amount for p in payments)
            context['total_due'] = total_due
            context['total_paid'] = total_paid
            context['total_owing'] = total_due - total_paid
        except Student.DoesNotExist:
            context['student'] = None
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in StudentFeesView: {str(e)}")
            context['student'] = None
            context['invoices'] = []
            context['payments'] = []
            context['academic_sessions'] = []
            context['terms'] = []
            context['selected_academic_session'] = ''
            context['selected_term'] = ''
            context['total_due'] = 0
            context['total_paid'] = 0
            context['total_owing'] = 0
        return context


class StudentDownloadReportCardView(LoginRequiredMixin, TemplateView):
    """Student download their report card as PDF"""
    template_name = 'students/portal/download_report_card.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from results.models import TermResult
            student = self.request.user.student_profile
            academic_session = self.request.GET.get('academic_session', '').strip()
            term_id = self.request.GET.get('term', '').strip()

            all_term_results = TermResult.objects.filter(student=student)
            term_results = all_term_results
            if academic_session:
                term_results = term_results.filter(term__academic_year=academic_session)
            if term_id:
                term_results = term_results.filter(term_id=term_id)

            from results.models import StudentResult
            context['student'] = student
            filtered_term_results = term_results.select_related('term', 'result_template').order_by('-term__academic_year', '-term__name')
            context['term_results'] = filtered_term_results
            context['results_by_term'] = {
                tr.id: StudentResult.objects.filter(
                    student=student,
                    term=tr.term,
                    result_template=tr.result_template
                ).select_related('class_subject__subject').order_by('class_subject__order')
                for tr in filtered_term_results
            }
            context['academic_sessions'] = all_term_results.order_by('term__academic_year').values_list('term__academic_year', flat=True).distinct()
            context['terms'] = Term.objects.filter(term_results__student=student).distinct().order_by('academic_year', 'name')
            selected_term_obj = Term.objects.filter(pk=term_id).first() if term_id else None
            context['selected_academic_session'] = academic_session
            context['selected_term'] = term_id
            context['selected_term_obj'] = selected_term_obj

            # Add invoices/payments for the selected session or term to support report card download views.
            from payroll.models import StudentInvoice, StudentPayment
            invoice_query = StudentInvoice.objects.filter(student=student)
            if academic_session:
                invoice_query = invoice_query.filter(academic_session=academic_session)
            if term_id:
                invoice_query = invoice_query.filter(term_id=term_id)
            context['invoices'] = invoice_query.order_by('-issued_date')
            context['payments'] = StudentPayment.objects.filter(invoice__in=context['invoices']).order_by('-payment_date')
        except Student.DoesNotExist:
            context['student'] = None
            context['term_results'] = []
            context['academic_sessions'] = []
            context['terms'] = []
            context['selected_academic_session'] = ''
            context['selected_term'] = ''
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in StudentDownloadReportCardView: {str(e)}")
            context['student'] = None
            context['term_results'] = []
            context['academic_sessions'] = []
            context['terms'] = []
            context['selected_academic_session'] = ''
            context['selected_term'] = ''
        return context
    
    def get(self, request, *args, **kwargs):
        try:
            context = self.get_context_data(**kwargs)
            student = context.get('student')

            # If PDF download is requested
            if request.GET.get('format') == 'pdf' and WEASYPRINT_AVAILABLE:
                from results.models import TermResult, StudentResult
                term_id = request.GET.get('term_id', '').strip()
                if not term_id:
                    messages.error(request, 'Please select a term before downloading a report card.')
                    return redirect('student_portal_report_card')

                selected_term = get_object_or_404(Term, pk=term_id)
                selected_term_result = TermResult.objects.filter(
                    student=student,
                    term=selected_term
                ).select_related('result_template').first()

                if selected_term_result:
                    selected_results = StudentResult.objects.filter(
                        student=student,
                        term=selected_term,
                        result_template=selected_term_result.result_template
                    ).select_related('class_subject__subject').order_by('class_subject__order')
                else:
                    selected_results = StudentResult.objects.filter(
                        student=student,
                        term=selected_term
                    ).select_related('class_subject__subject').order_by('class_subject__order')

                context['selected_term'] = term_id
                context['selected_term_obj'] = selected_term
                context['selected_term_result'] = selected_term_result
                context['selected_results'] = selected_results

                from results.models import StudentConduct
                from attendance.models import AttendanceRecord
                context['student_conduct'] = StudentConduct.objects.filter(student=student, term=selected_term).first()
                attendance_records = AttendanceRecord.objects.filter(
                    student=student,
                    date__gte=selected_term.start_date,
                    date__lte=selected_term.end_date
                ) if selected_term.start_date and selected_term.end_date else AttendanceRecord.objects.none()
                attendance_sessions = attendance_records.count()
                attended_sessions = sum(record.present_sessions for record in attendance_records)
                total_sessions = attendance_sessions * 2
                attendance_percentage = round((attended_sessions / total_sessions) * 100, 2) if total_sessions > 0 else None

                if (attendance_percentage is None or attendance_sessions == 0) and context['student_conduct']:
                    if getattr(context['student_conduct'], 'manual_attendance_percentage', None) is not None:
                        attendance_percentage = float(context['student_conduct'].manual_attendance_percentage)
                        attended_sessions = context['student_conduct'].manual_attendance_sessions_attended or attended_sessions
                        total_sessions = context['student_conduct'].manual_attendance_total_sessions or total_sessions
                        attendance_sessions = context['student_conduct'].manual_attendance_days_marked or attendance_sessions

                context['attendance_sessions'] = attendance_sessions
                context['attended_sessions'] = attended_sessions
                context['attendance_total_sessions'] = total_sessions
                context['attendance_percentage'] = attendance_percentage
                context['attendance_percentage_str'] = None if attendance_percentage is None else str(attendance_percentage)
                context['has_attendance'] = (
                    attendance_sessions > 0 or
                    (context['student_conduct'] is not None and getattr(context['student_conduct'], 'manual_attendance_percentage', None) is not None) or
                    (attendance_percentage is not None)
                )

                html_string = render_to_string('students/portal/report_card_pdf.html', context)
                html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
                pdf = html.write_pdf()
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="report_card_{student.admission_no}_{selected_term.name}.pdf"'
                return response
        except Student.DoesNotExist:
            messages.error(request, 'Student profile not found.')
            return redirect('student_portal_dashboard')

        return super().get(request, *args, **kwargs)


class StudentClassTimetableView(LoginRequiredMixin, TemplateView):
    """Student view their class timetable"""
    template_name = 'students/portal/class_timetable.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            student = self.request.user.student_profile
            context['student'] = student
            context['class'] = student.student_class
            
            # Get class subjects for the student's current class
            if student.student_class:
                from exams.models import ClassSubject
                context['class_subjects'] = ClassSubject.objects.filter(
                    school_class=student.student_class
                ).select_related('subject').order_by('order')
            else:
                context['class_subjects'] = []
        except Student.DoesNotExist:
            context['student'] = None
            context['class'] = None
            context['class_subjects'] = []
        return context


class StudentClassAnnouncementsView(LoginRequiredMixin, TemplateView):
    """Student view class announcements"""
    template_name = 'students/portal/class_announcements.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from announcements.models import Announcement
            student = self.request.user.student_profile
            context['student'] = student
            
            # Get announcements for the student's class
            if student.student_class:
                context['announcements'] = Announcement.objects.filter(
                    school_class=student.student_class,
                    is_published=True
                ).select_related('created_by').order_by('-created_at')
            else:
                context['announcements'] = []
        except Student.DoesNotExist:
            context['student'] = None
            context['announcements'] = []
        return context


class StudentAttendanceView(LoginRequiredMixin, TemplateView):
    """Student view their own attendance records"""
    template_name = 'students/portal/student_attendance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from attendance.models import AttendanceRecord
            student = self.request.user.student_profile
            context['student'] = student
            
            # Get attendance records for this student
            context['attendance_records'] = AttendanceRecord.objects.filter(
                student=student
            ).select_related('school_class').order_by('-date')
            
            # Calculate attendance summary
            total_records = context['attendance_records'].count()
            present_count = context['attendance_records'].filter(present=True).count()
            absent_count = context['attendance_records'].filter(present=False).count()
            
            context['total_sessions'] = total_records
            context['present_count'] = present_count
            context['absent_count'] = absent_count
            context['attendance_percentage'] = (present_count / total_records * 100) if total_records > 0 else 0
        except Student.DoesNotExist:
            context['student'] = None
            context['attendance_records'] = []
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in StudentAttendanceView: {str(e)}")
            context['student'] = None
            context['attendance_records'] = []
        return context


class StudentContactTeacherView(LoginRequiredMixin, TemplateView):
    """Student contact teachers through portal messages"""
    template_name = 'students/portal/contact_teacher.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from school_classes.models import ClassTeacher
            student = self.request.user.student_profile
            context['student'] = student
            
            # Get teachers for the student's class
            if student.student_class:
                context['teachers'] = ClassTeacher.objects.filter(
                    school_class=student.student_class,
                    is_active=True
                ).select_related('teacher__user', 'subject').order_by('teacher__user__first_name')
            else:
                context['teachers'] = []
        except Student.DoesNotExist:
            context['student'] = None
            context['teachers'] = []
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in StudentContactTeacherView: {str(e)}")
            context['student'] = None
            context['teachers'] = []
        return context


# ==================== ADMIN: STUDENT PERMISSIONS ====================

def user_is_admin(user):
    """Check if user is admin/staff"""
    try:
        return user.is_staff or user.groups.filter(name__in=['Admin', 'Staff']).exists()
    except:
        return False


@login_required
def grant_student_permission(request, student_id, permission_code):
    """Admin grants a permission to a student"""
    from .models import StudentPermission
    
    if not user_is_admin(request.user):
        return HttpResponseForbidden('You do not have permission.')
    
    student = get_object_or_404(Student, pk=student_id)
    perm, _ = StudentPermission.objects.get_or_create(
        student=student,
        permission=permission_code
    )
    perm.is_granted = True
    perm.granted_by = request.user
    perm.save()

    perm_display = dict(StudentPermission.PERMISSION_CHOICES).get(permission_code)
    messages.success(
        request,
        f'Permission "{perm_display}" granted to {student.full_name()}.'
    )
    return redirect('student_permissions_detail', student_id=student_id)


@login_required
def revoke_student_permission(request, student_id, permission_code):
    """Admin revokes a permission from a student"""
    from .models import StudentPermission
    
    if not user_is_admin(request.user):
        return HttpResponseForbidden('You do not have permission.')

    student = get_object_or_404(Student, pk=student_id)
    perm, _ = StudentPermission.objects.get_or_create(
        student=student,
        permission=permission_code
    )
    perm.is_granted = False
    perm.save()

    perm_display = dict(StudentPermission.PERMISSION_CHOICES).get(permission_code)
    messages.success(
        request,
        f'Permission "{perm_display}" revoked from {student.full_name()}.'
    )
    return redirect('student_permissions_detail', student_id=student_id)


class StudentPermissionsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Admin manages student permissions"""
    from .models import StudentPermission
    
    template_name = 'students/admin/permissions_list.html'
    context_object_name = 'permissions'
    paginate_by = 50

    def test_func(self):
        return user_is_admin(self.request.user)

    def get_queryset(self):
        from .models import StudentPermission
        student_id = self.kwargs.get('student_id')
        if student_id:
            return StudentPermission.objects.filter(
                student_id=student_id
            ).select_related('student__user', 'granted_by')
        return StudentPermission.objects.select_related(
            'student__user', 'granted_by'
        ).order_by('-granted_at')

    def get_context_data(self, **kwargs):
        from .models import StudentPermission
        context = super().get_context_data(**kwargs)
        
        student_id = self.kwargs.get('student_id')
        if student_id:
            try:
                student = Student.objects.get(pk=student_id)
                context['student'] = student
                context['all_permissions'] = StudentPermission.PERMISSION_CHOICES
            except Student.DoesNotExist:
                pass
        
        context['students'] = Student.objects.filter(
            user__is_active=True
        ).select_related('user', 'student_class').order_by('surname', 'other_names')
        
        return context


class BulkStudentPermissionView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin bulk assign/revoke permissions for students"""
    template_name = 'students/admin/bulk_permissions.html'

    def test_func(self):
        return user_is_admin(self.request.user)

    def get_context_data(self, **kwargs):
        from .models import StudentPermission
        context = super().get_context_data(**kwargs)
        context['students'] = Student.objects.filter(
            user__is_active=True
        ).select_related('user').order_by('surname', 'other_names')
        context['permission_choices'] = StudentPermission.PERMISSION_CHOICES
        
        # If a student is selected, show their current permissions
        student_id = self.request.GET.get('student_id')
        if student_id:
            try:
                student = Student.objects.get(pk=student_id)
                context['selected_student'] = student
                
                # Get all permissions with their current granted status for this student
                from .models import StudentPermission
                granted_perms = StudentPermission.objects.filter(
                    student=student,
                    is_granted=True
                ).values_list('permission', flat=True)
                context['granted_permissions'] = list(granted_perms)
            except Student.DoesNotExist:
                pass
        
        return context

    def post(self, request, *args, **kwargs):
        from .models import StudentPermission
        from django.http import HttpResponseForbidden
        
        student_id = request.POST.get('student_id')
        if not student_id:
            messages.error(request, 'Please select a student.')
            return redirect('bulk_student_permissions')
        
        student = get_object_or_404(Student, pk=student_id)
        
        # Get all selected permissions from the form
        selected_permissions = request.POST.getlist('permissions')
        
        # Grant/Revoke all permissions based on checkbox state
        for code, name in StudentPermission.PERMISSION_CHOICES:
            perm_obj, _ = StudentPermission.objects.get_or_create(
                student=student,
                permission=code
            )
            is_granted = code in selected_permissions
            perm_obj.is_granted = is_granted
            perm_obj.granted_by = request.user
            perm_obj.save()

        messages.success(
            request,
            f'Permissions updated for {student.full_name()}.'
        )
        return redirect('student_permissions_detail', student_id=student_id)
