import math

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from django.db.models import Avg, Count, Sum, Q, Max, Min
from django.views.generic import TemplateView, ListView
from django.utils.decorators import method_decorator
from students.models import Student
from exams.models import Term, ClassSubject
from school_classes.models import SchoolClasses, ClassTeacher, Teacher
from attendance.models import AttendanceRecord
from .models import (
    StudentResult, TermResult, ResultTemplate,
    GradeScale, Promotion, ReportCardComment, StudentConduct
)



def user_profile_approved(user):
    """Defensively check if user profile is approved"""
    try:
        return user.profile.is_approved
    except AttributeError:
        return False


def user_is_staff(user):
    """Check if user is staff/teacher"""
    try:
        return (
            user.profile.is_approved and
            user.groups.filter(name__in=['Teacher', 'Staff']).exists()
        )
    except AttributeError:
        return False


def get_next_school_class(source_class):
    """Find the next class in ordering for bulk promotion."""
    ordered_classes = list(SchoolClasses.objects.order_by('level', 'class_name'))
    for index, cls in enumerate(ordered_classes):
        if cls.pk == source_class.pk:
            return ordered_classes[index + 1] if index + 1 < len(ordered_classes) else None
    return None


def generate_distinct_chart_colors(label_count):
    """Create a palette of distinct colors for each chart label."""
    label_count = max(int(label_count or 0), 1)
    colors = []
    for index in range(label_count):
        hue = (index * 360 / label_count) % 360
        colors.append(f"hsl({hue}, 70%, 45%)")
    return colors


@login_required
def results_home(request):
    """Main results dashboard"""
    if not user_profile_approved(request.user):
        messages.error(request, 'Your account is not approved yet.')
        return redirect('home')

    # Get active terms
    active_terms = Term.objects.filter(is_active=True)

    # Get classes with results
    classes_with_results = SchoolClasses.objects.filter(
        students__results__isnull=False
    ).distinct()

    context = {
        'active_terms': active_terms,
        'classes_with_results': classes_with_results,
    }

    return render(request, 'results/results_home.html', context)


@login_required
def select_class_for_report_card(request):
    """Select class and term to view report cards"""
    if not user_profile_approved(request.user):
        messages.error(request, 'Your account is not approved yet.')
        return redirect('home')

    if request.method == 'POST':
        class_id = request.POST.get('school_class')
        term_id = request.POST.get('term')
        
        if class_id and term_id:
            return redirect('report_card_student_list', class_id=class_id, term_id=term_id)
        else:
            messages.error(request, 'Please select both class and term.')

    # Get available classes
    if request.user.is_staff or request.user.is_superuser:
        # Admins see all classes
        classes = SchoolClasses.objects.all().order_by('class_name')
    elif user_is_staff(request.user):
        # Teachers see only assigned classes
        try:
            teacher_instance = request.user.teacher_profile
            classes = SchoolClasses.objects.filter(
                teachers__teacher=teacher_instance
            ).distinct().order_by('class_name')
        except Teacher.DoesNotExist:
            classes = SchoolClasses.objects.none()
    else:
        # Non-staff users can access their own class if they're a student
        if hasattr(request.user, 'student'):
            classes = SchoolClasses.objects.filter(id=request.user.student.student_class_id)
        else:
            classes = SchoolClasses.objects.none()

    # Get active terms
    terms = Term.objects.filter(is_active=True).order_by('academic_year')

    context = {
        'classes': classes,
        'terms': terms,
    }

    return render(request, 'results/select_class_for_report_card.html', context)


@login_required
def report_card_student_list(request, class_id, term_id):
    """List students in a class for viewing their report cards"""
    if not user_profile_approved(request.user):
        messages.error(request, 'Your account is not approved yet.')
        return redirect('home')

    school_class = get_object_or_404(SchoolClasses, pk=class_id)
    term = get_object_or_404(Term, pk=term_id)

    # Check permission - teachers can only view their assigned classes, admins can view all
    if request.user.is_staff or request.user.is_superuser:
        # Admins have access to all classes
        pass
    elif user_is_staff(request.user):
        try:
            teacher_instance = request.user.teacher_profile
            has_permission = ClassTeacher.objects.filter(
                teacher=teacher_instance, 
                school_class=school_class
            ).exists()
            if not has_permission:
                messages.error(request, 'You do not have permission to view this class.')
                return redirect('select_class_for_report_card')
        except Teacher.DoesNotExist:
            messages.error(request, 'You do not have permission to view this class.')
            return redirect('select_class_for_report_card')
    else:
        # Students can view their own class
        if not (hasattr(request.user, 'student') and request.user.student.student_class == school_class):
            messages.error(request, 'You do not have permission to view this class.')
            return redirect('select_class_for_report_card')

    # Optional academic session, term, and student filters from GET
    academic_session = request.GET.get('academic_session', '').strip()
    selected_term_id = request.GET.get('term', '').strip()
    selected_student_id = request.GET.get('student', '').strip()
    selected_term = None
    selected_student = None
    if selected_term_id:
        try:
            selected_term = Term.objects.get(pk=selected_term_id)
        except Term.DoesNotExist:
            selected_term_id = ''
    if selected_student_id:
        try:
            selected_student = Student.objects.get(pk=selected_student_id)
        except Student.DoesNotExist:
            selected_student_id = ''

    display_term = selected_term or term

    # Check if result template exists for the current display term
    try:
        result_template = ResultTemplate.objects.get(
            school_class=school_class,
            term=display_term,
            is_active=True
        )
    except ResultTemplate.DoesNotExist:
        messages.warning(request, 'No result template found for this class and term.')
        result_template = None

    # Build the student list from the selected filters
    student_results_qs = StudentResult.objects.filter(
        class_subject__school_class=school_class,
        percentage__isnull=False,
    )
    if academic_session:
        student_results_qs = student_results_qs.filter(term__academic_year=academic_session)
    if selected_term:
        student_results_qs = student_results_qs.filter(term=selected_term)
    elif display_term:
        student_results_qs = student_results_qs.filter(term=display_term)
    if selected_student:
        student_results_qs = student_results_qs.filter(student=selected_student)

    student_ids = list(student_results_qs.values_list('student_id', flat=True).distinct())
    students_base = Student.objects.filter(
        Q(student_class=school_class, status='active') |
        Q(results__class_subject__school_class=school_class) |
        Q(term_results__result_template__school_class=school_class)
    ).distinct()

    if selected_student:
        students = students_base.filter(pk=selected_student.id).order_by('surname', 'other_names')
    elif student_ids:
        students = students_base.filter(pk__in=student_ids).order_by('surname', 'other_names')
    elif academic_session or selected_term_id or selected_student_id:
        students = Student.objects.none()
    else:
        students = students_base.filter(
            Q(student_class=school_class, status='active') |
            Q(results__class_subject__school_class=school_class, results__term=display_term) |
            Q(term_results__term=display_term, term_results__result_template__school_class=school_class)
        ).distinct().order_by('surname', 'other_names')

    # Build performance aggregates for the class based on the active filters
    performance_summary = {}
    performance_by_term = []
    top_subjects = []
    chart_labels = []
    chart_data = []
    chart_title = 'Student Performance Across Sessions'
    chart_series_label = 'Average Percentage'
    chart_x_label = 'Student'
    chart_type = request.GET.get('chart_type', 'bar').strip().lower() or 'bar'

    chart_results = StudentResult.objects.filter(
        class_subject__school_class=school_class,
        percentage__isnull=False,
    )
    if academic_session:
        chart_results = chart_results.filter(term__academic_year=academic_session)
    if selected_term:
        chart_results = chart_results.filter(term=selected_term)
    if selected_student:
        chart_results = chart_results.filter(student=selected_student)

    published_results = chart_results
    avg_pct = published_results.aggregate(avg=Avg('percentage'))['avg'] or 0
    result_count = published_results.count()

    performance_summary = {
        'result_count': result_count,
        'average_percentage': round(float(avg_pct), 2) if avg_pct else 0,
        'highest_percentage': published_results.aggregate(max_percent=Max('percentage'))['max_percent'] or 0,
        'lowest_percentage': published_results.aggregate(min_percent=Min('percentage'))['min_percent'] or 0,
    }

    if selected_term:
        top_subjects = published_results.values('class_subject__subject__name').annotate(
            avg_percentage=Avg('percentage')
        ).order_by('-avg_percentage')[:10]
        chart_labels = [item['class_subject__subject__name'] for item in top_subjects]
        chart_data = [round(float(item['avg_percentage'] or 0), 2) for item in top_subjects]
        performance_by_term = []
        chart_title = f'Subject Performance for {selected_term.display_name} ({selected_term.academic_year})'
        chart_series_label = 'Average Percentage'
        chart_x_label = 'Subject'
    elif selected_student:
        performance_by_term = published_results.values(
            'term__id', 'term__display_name', 'term__academic_year'
        ).annotate(avg_percentage=Avg('percentage')).order_by('term__academic_year', 'term__name')
        chart_labels = [f"{item['term__display_name']} ({item['term__academic_year']})" for item in performance_by_term]
        chart_data = [round(float(item['avg_percentage'] or 0), 2) for item in performance_by_term]
        top_subjects = published_results.values('class_subject__subject__name').annotate(
            avg_percentage=Avg('percentage')
        ).order_by('-avg_percentage')[:5]
        chart_title = f'Performance for {selected_student.full_name()} across terms'
        chart_series_label = 'Average Percentage'
        chart_x_label = 'Term'
    elif academic_session:
        performance_by_term = published_results.values(
            'term__id', 'term__display_name', 'term__academic_year'
        ).annotate(avg_percentage=Avg('percentage')).order_by('term__academic_year', 'term__name')
        chart_labels = [f"{item['term__display_name']} ({item['term__academic_year']})" for item in performance_by_term]
        chart_data = [round(float(item['avg_percentage'] or 0), 2) for item in performance_by_term]
        top_subjects = published_results.values('class_subject__subject__name').annotate(
            avg_percentage=Avg('percentage')
        ).order_by('-avg_percentage')[:5]
        chart_title = f'Performance Across Terms for {academic_session}'
        chart_series_label = 'Average Percentage'
        chart_x_label = 'Term'
    else:
        performance_by_term = published_results.values(
            'student__id', 'student__surname', 'student__other_names'
        ).annotate(avg_percentage=Avg('percentage')).order_by('student__surname', 'student__other_names')
        chart_labels = [
            ' '.join(filter(None, [item['student__surname'], item['student__other_names']])).strip() or f'Student {idx + 1}'
            for idx, item in enumerate(performance_by_term)
        ]
        chart_data = [round(float(item['avg_percentage'] or 0), 2) for item in performance_by_term]
        top_subjects = published_results.values('class_subject__subject__name').annotate(
            avg_percentage=Avg('percentage')
        ).order_by('-avg_percentage')[:5]

    chart_colors = generate_distinct_chart_colors(len(chart_labels))

    context = {
        'school_class': school_class,
        'term': display_term,
        'students': students,
        'result_template': result_template,
        'academic_sessions': Term.objects.order_by('academic_year').values_list('academic_year', flat=True).distinct(),
        'selected_academic_session': academic_session,
        'students_for_filter': students_base.order_by('surname', 'other_names'),
        'selected_student': selected_student,
        'selected_student_id': selected_student_id,
        'terms': Term.objects.order_by('academic_year', 'name'),
        'selected_term': selected_term_id,
        'performance_summary': performance_summary,
        'performance_by_term': list(performance_by_term),
        'top_subjects': list(top_subjects),
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'chart_title': chart_title,
        'chart_series_label': chart_series_label,
        'chart_x_label': chart_x_label,
        'chart_type': chart_type,
        'chart_colors': chart_colors,
    }

    return render(request, 'results/report_card_student_list.html', context)


@login_required
def class_results(request, class_id, term_id):
    """View results for a specific class and term"""
    if not user_profile_approved(request.user):
        messages.error(request, 'Your account is not approved yet.')
        return redirect('home')

    school_class = get_object_or_404(SchoolClasses, pk=class_id)
    term = get_object_or_404(Term, pk=term_id)

    # Get result template for this class and term
    try:
        result_template = ResultTemplate.objects.get(
            school_class=school_class,
            term=term,
            is_active=True
        )
    except ResultTemplate.DoesNotExist:
        messages.error(request, f'No result template found for {school_class} - {term}')
        return redirect('results_home')

    # Get all students for this class and term, including historical students with results for the selected class.
    students = Student.objects.filter(
        Q(student_class=school_class, status='active') |
        Q(results__class_subject__school_class=school_class, results__term=term) |
        Q(term_results__term=term, term_results__result_template__school_class=school_class)
    ).distinct().order_by('surname', 'other_names')

    # Get results for each student
    student_results = []
    for student in students:
        results = StudentResult.objects.filter(
            student=student,
            term=term,
            result_template=result_template
        ).select_related('class_subject__subject')

        # Calculate term aggregates
        term_result, created = TermResult.objects.get_or_create(
            student=student,
            term=term,
            result_template=result_template,
            defaults={'is_complete': False}
        )

        if results.exists() and not term_result.is_complete:
            term_result.calculate_aggregates()

        student_results.append({
            'student': student,
            'results': results,
            'term_result': term_result,
        })

    can_print_broadsheet = False
    broadsheet_url = None

    if request.user.is_staff or request.user.is_superuser:
        can_print_broadsheet = True
        broadsheet_url = reverse('broadsheet', args=[class_id, term_id])
    elif user_is_staff(request.user):
        try:
            teacher = request.user.teacher_profile
            if ClassTeacher.objects.filter(teacher=teacher, school_class=school_class).exists():
                from school_classes.models import TeacherPermission
                if teacher_has_permission(teacher, 'print_broadsheet'):
                    can_print_broadsheet = True
                    broadsheet_url = reverse('teacher_print_broadsheet', args=[class_id, term_id])
        except Exception:
            pass

    context = {
        'school_class': school_class,
        'term': term,
        'result_template': result_template,
        'student_results': student_results,
        'can_modify': user_is_staff(request.user),
        'can_print_broadsheet': can_print_broadsheet,
        'broadsheet_url': broadsheet_url,
        'academic_sessions': Term.objects.filter(termresult__result_template__school_class=school_class).order_by('academic_year').values_list('academic_year', flat=True).distinct(),
        'selected_academic_session': request.GET.get('academic_session', '').strip(),
        'terms': Term.objects.filter(is_active=True).order_by('academic_year', 'name'),
        'selected_term': term.id if term else '',
        # Performance placeholders (calculated elsewhere or empty)
        'performance_summary': {},
        'performance_by_term': [],
        'top_subjects': [],
        'chart_labels': [],
        'chart_data': [],
    }

    return render(request, 'results/class_results.html', context)


@login_required
def student_report_card(request, student_id, term_id):
    """Generate individual student report card"""
    if not user_profile_approved(request.user):
        messages.error(request, 'Your account is not approved yet.')
        return redirect('home')

    student = get_object_or_404(Student, pk=student_id)
    term = get_object_or_404(Term, pk=term_id)

    # Check if user can view this student's results
    if not (request.user.is_staff or request.user.is_superuser or user_is_staff(request.user) or student.admission_no == request.user.username):
        messages.error(request, 'You do not have permission to view this report card.')
        return redirect('home')

    # Get student results for the selected term, preserving historical class/template context.
    results = StudentResult.objects.filter(
        student=student,
        term=term
    ).select_related('class_subject__subject', 'result_template').order_by('class_subject__order')

    result_template = None
    if results.exists():
        result_template = results.first().result_template
    else:
        result_template = ResultTemplate.objects.filter(
            school_class=student.student_class,
            term=term,
            is_active=True
        ).first()

    term_result = None
    if result_template:
        term_result, created = TermResult.objects.get_or_create(
            student=student,
            term=term,
            defaults={'result_template': result_template, 'is_complete': False}
        )
    else:
        term_result = TermResult.objects.filter(student=student, term=term).first()

    if term_result and results.exists() and not term_result.is_complete:
        term_result.calculate_aggregates()

    # Get student conduct record
    student_conduct = StudentConduct.objects.filter(
        student=student,
        term=term
    ).first()

    # Attendance summary for the term
    attendance_records = AttendanceRecord.objects.filter(
        student=student,
        date__gte=term.start_date,
        date__lte=term.end_date
    ) if term.start_date and term.end_date else AttendanceRecord.objects.none()

    # Invoice and receipt details for the selected term or academic year
    invoices = []
    payments = []
    try:
        from payroll.models import StudentInvoice, StudentPayment
        invoices = StudentInvoice.objects.filter(
            student=student
        ).filter(
            Q(term=term) | Q(academic_session=term.academic_year)
        ).order_by('-issued_date')
        payments = StudentPayment.objects.filter(
            invoice__in=invoices
        ).order_by('-payment_date')
    except Exception:
        invoices = []
        payments = []

    # Calculate automatic attendance if records exist
    attendance_sessions = attendance_records.count()
    attended_sessions = sum(record.present_sessions for record in attendance_records)
    total_sessions = attendance_sessions * 2
    attendance_percentage = round((attended_sessions / total_sessions) * 100, 2) if total_sessions > 0 else None

    # Fallback to manual override stored on StudentConduct when automatic data missing
    if (attendance_percentage is None or attendance_sessions == 0) and student_conduct:
        if student_conduct.manual_attendance_percentage is not None:
            attendance_percentage = float(student_conduct.manual_attendance_percentage)
            attended_sessions = student_conduct.manual_attendance_sessions_attended or attended_sessions
            total_sessions = student_conduct.manual_attendance_total_sessions or total_sessions
            attendance_sessions = student_conduct.manual_attendance_days_marked or attendance_sessions

    # Determine whether we have attendance data to show (automatic or manual)
    has_attendance = (attendance_sessions > 0) or (
        student_conduct is not None and getattr(student_conduct, 'manual_attendance_percentage', None) is not None
    ) or (attendance_percentage is not None)

    context = {
        'student': student,
        'term': term,
        'result_template': result_template,
        'results': results,
        'term_result': term_result,
        'student_conduct': student_conduct,
        'attendance_records': attendance_records,
        'attendance_sessions': attendance_sessions,
        'attendance_total_sessions': total_sessions,
        'attended_sessions': attended_sessions,
        'attendance_percentage': attendance_percentage,
        'has_attendance': has_attendance,
        'invoices': invoices,
        'payments': payments,
    }
    # Prepare a string for display that preserves 0 as valid value
    context['attendance_percentage_str'] = None if attendance_percentage is None else str(attendance_percentage)

    return render(request, 'results/student_report_card.html', context)


@login_required
def broadsheet(request, class_id, term_id):
    """Generate printable broadsheet for a class"""
    if not (request.user.is_staff or request.user.is_superuser or user_is_staff(request.user)):
        messages.error(request, 'You do not have permission to view broadsheets.')
        return redirect('home')

    school_class = get_object_or_404(SchoolClasses, pk=class_id)
    term = get_object_or_404(Term, pk=term_id)

    # Get result template
    try:
        result_template = ResultTemplate.objects.get(
            school_class=school_class,
            term=term,
            is_active=True
        )
    except ResultTemplate.DoesNotExist:
        messages.error(request, f'No result template found for {school_class} - {term}')
        return redirect('results_home')

    # Allow optional filtering by academic session / term via GET params
    academic_session = request.GET.get('academic_session', '').strip()
    term_param = request.GET.get('term', '').strip()
    if term_param:
        # override term if a GET term param is provided
        try:
            term = Term.objects.get(pk=term_param)
        except Term.DoesNotExist:
            pass

    # Get all subjects for this class
    class_subjects = ClassSubject.objects.filter(
        school_class=school_class
    ).select_related('subject').order_by('order')

    # Get all students
    students = Student.objects.filter(
        student_class=school_class,
        status='active'
    ).order_by('surname', 'other_names')

    # Build broadsheet data (respect filters)
    broadsheet_data = []

    # Build a base StudentResult queryset for aggregation and per-student lookups
    base_results_qs = StudentResult.objects.filter(
        result_template=result_template,
        class_subject__school_class=school_class
    )
    if academic_session:
        base_results_qs = base_results_qs.filter(term__academic_year=academic_session)
    if term:
        base_results_qs = base_results_qs.filter(term=term)

    for student in students:
        student_data = {
            'student': student,
            'subject_scores': {},
            'term_result': None,
        }

        # Get results for each subject for this student
        for class_subject in class_subjects:
            result = base_results_qs.filter(
                student=student,
                class_subject=class_subject
            ).select_related('class_subject__subject').first()

            if result:
                student_data['subject_scores'][class_subject.subject.name] = {
                    'test_score': result.test_score,
                    'exam_score': result.exam_score,
                    'total_score': result.total_score,
                    'grade': result.grade,
                }
            else:
                student_data['subject_scores'][class_subject.subject.name] = None

        # Get term result
        term_result = TermResult.objects.filter(
            student=student,
            term=term,
            result_template=result_template
        ).first()
        if term_result and not term_result.is_complete:
            term_result.calculate_aggregates()
        student_data['term_result'] = term_result

        broadsheet_data.append(student_data)

    # Aggregate performance summary for the class using the filtered results
    published_results = base_results_qs.filter(percentage__isnull=False)
    avg_pct = published_results.aggregate(avg=Avg('percentage'))['avg'] or 0
    result_count = published_results.count()

    performance_by_term = published_results.values(
        'term__id', 'term__display_name', 'term__academic_year'
    ).annotate(
        avg_percentage=Avg('percentage'),
        total_score=Sum('total_score')
    ).order_by('term__academic_year', 'term__name')

    top_subjects = published_results.values('class_subject__subject__name').annotate(
        avg_percentage=Avg('percentage')
    ).order_by('-avg_percentage')[:5]

    context = {
        'school_class': school_class,
        'term': term,
        'result_template': result_template,
        'class_subjects': class_subjects,
        'broadsheet_data': broadsheet_data,
        'academic_sessions': Term.objects.filter(termresult__result_template__school_class=school_class).order_by('academic_year').values_list('academic_year', flat=True).distinct(),
        'selected_academic_session': academic_session,
        'selected_term': term.id if term else '',
        'performance_summary': {
            'result_count': result_count,
            'average_percentage': round(float(avg_pct), 2) if avg_pct else 0,
            'highest_percentage': published_results.aggregate(max_percent=Max('percentage'))['max_percent'] or 0,
            'lowest_percentage': published_results.aggregate(min_percent=Min('percentage'))['min_percent'] or 0,
        },
        'performance_by_term': list(performance_by_term),
        'top_subjects': list(top_subjects),
        'chart_labels': [f"{item['term__display_name']} {item['term__academic_year']}" for item in performance_by_term],
        'chart_data': [round(float(item['avg_percentage'] or 0), 2) for item in performance_by_term],
    }

    return render(request, 'results/broadsheet.html', context)


@login_required
def student_results_by_admission(request):
    """Allow students to view their results by admission number"""
    if request.method == 'POST':
        admission_no = request.POST.get('admission_no', '').strip()

        if not admission_no:
            messages.error(request, 'Please enter an admission number.')
            return redirect('home')

        try:
            student = Student.objects.get(admission_no=admission_no)
        except Student.DoesNotExist:
            messages.error(request, 'Student not found with this admission number.')
            return redirect('home')

        # Get active terms
        active_terms = Term.objects.filter(is_active=True)

        context = {
            'student': student,
            'active_terms': active_terms,
        }

        return render(request, 'results/student_results_lookup.html', context)

    return render(request, 'results/student_results_lookup.html')


# Legacy views for backward compatibility
@login_required
def report_card(request, student_id, exam_id):
    """Legacy view for backward compatibility"""
    messages.info(request, 'This feature has been updated. Please use the new results system.')
    return redirect('results_home')


@login_required
def promotions_list(request):
    if not (request.user.is_staff or request.user.is_superuser or user_is_staff(request.user)):
        messages.error(request, 'You do not have permission to view promotions.')
        return redirect('home')

    promotions = Promotion.objects.select_related(
        'student', 'from_class', 'to_class', 'term'
    ).order_by('-promoted_date')

    classes = SchoolClasses.objects.all().order_by('class_name')
    terms = Term.objects.filter(is_active=True).order_by('academic_year', 'name')
    students = Student.objects.select_related('student_class').filter(status='active').order_by('surname', 'other_names', 'admission_no')

    selected_student_ids = []
    if request.method == 'POST':
        source_class_id = request.POST.get('source_class') or ''
        target_class_id = request.POST.get('target_class')
        term_id = request.POST.get('term')
        percentage_value = (request.POST.get('percentage') or '').strip()
        remarks = (request.POST.get('remarks') or '').strip()
        selected_student_ids = request.POST.getlist('student_ids')

        if not target_class_id and not selected_student_ids:
            if not source_class_id:
                messages.error(request, 'Choose a source class or select students individually.')
                return render(request, 'results/promotions_list.html', {
                    'promotions': promotions,
                    'classes': classes,
                    'terms': terms,
                    'students': students,
                    'selected_student_ids': selected_student_ids,
                })

            source_class = get_object_or_404(SchoolClasses, pk=source_class_id)
            target_class = get_next_school_class(source_class)
            if not target_class:
                messages.error(request, 'Unable to determine the next class for bulk promotion. Please select a destination class manually.')
                return render(request, 'results/promotions_list.html', {
                    'promotions': promotions,
                    'classes': classes,
                    'terms': terms,
                    'students': students,
                    'selected_student_ids': selected_student_ids,
                })
        elif not target_class_id:
            messages.error(request, 'Please select a destination class for individual promotion.')
            return render(request, 'results/promotions_list.html', {
                'promotions': promotions,
                'classes': classes,
                'terms': terms,
                'students': students,
                'selected_student_ids': selected_student_ids,
            })
        else:
            target_class = get_object_or_404(SchoolClasses, pk=target_class_id)

        term = get_object_or_404(Term, pk=term_id) if term_id else terms.first()
        if not term:
            messages.error(request, 'No active term is available for promotion.')
            return render(request, 'results/promotions_list.html', {
                'promotions': promotions,
                'classes': classes,
                'terms': terms,
                'students': students,
                'selected_student_ids': selected_student_ids,
            })

        if source_class_id and str(source_class_id) == str(target_class_id):
            messages.error(request, 'The source class and destination class cannot be the same.')
            return render(request, 'results/promotions_list.html', {
                'promotions': promotions,
                'classes': classes,
                'terms': terms,
                'students': students,
                'selected_student_ids': selected_student_ids,
            })

        student_queryset = Student.objects.select_related('student_class').filter(status='active')
        if source_class_id:
            student_queryset = student_queryset.filter(student_class_id=source_class_id)
        if selected_student_ids:
            student_queryset = student_queryset.filter(pk__in=selected_student_ids)

        eligible_students = list(student_queryset.order_by('surname', 'other_names', 'admission_no'))

        if selected_student_ids:
            students_to_promote = [student for student in eligible_students if str(student.pk) in selected_student_ids]
        elif percentage_value:
            try:
                percentage = float(percentage_value)
            except ValueError:
                messages.error(request, 'Please enter a valid percentage value.')
                return render(request, 'results/promotions_list.html', {
                    'promotions': promotions,
                    'classes': classes,
                    'terms': terms,
                    'students': students,
                    'selected_student_ids': selected_student_ids,
                })

            if percentage <= 0 or percentage > 100:
                messages.error(request, 'Percentage must be between 1 and 100.')
                return render(request, 'results/promotions_list.html', {
                    'promotions': promotions,
                    'classes': classes,
                    'terms': terms,
                    'students': students,
                    'selected_student_ids': selected_student_ids,
                })

            if not eligible_students:
                messages.error(request, 'No students are available for promotion from the selected class.')
                return render(request, 'results/promotions_list.html', {
                    'promotions': promotions,
                    'classes': classes,
                    'terms': terms,
                    'students': students,
                    'selected_student_ids': selected_student_ids,
                })

            count = max(1, math.ceil(len(eligible_students) * percentage / 100))
            students_to_promote = eligible_students[:count]
        else:
            students_to_promote = eligible_students

        if not students_to_promote:
            messages.error(request, 'No students were selected for promotion.')
            return render(request, 'results/promotions_list.html', {
                'promotions': promotions,
                'classes': classes,
                'terms': terms,
                'students': students,
                'selected_student_ids': selected_student_ids,
            })

            promoted_count = 0
            for student in students_to_promote:
                current_class = student.student_class
                if not current_class:
                    continue
                if current_class.id == target_class.id:
                    continue

                student.student_class = target_class
                student.save(update_fields=['student_class'])
                Promotion.objects.create(
                    student=student,
                    from_class=current_class,
                    to_class=target_class,
                    term=term,
                    remarks=remarks,
                    promoted_by=request.user
                )
                promoted_count += 1

            if promoted_count:
                messages.success(request, f'Successfully promoted {promoted_count} student(s) to {target_class}.')
            else:
                messages.info(request, 'No changes were made because the selected students were already in the destination class.')
            return redirect('promotions_list')

    return render(request, 'results/promotions_list.html', {
        'promotions': promotions,
        'classes': classes,
        'terms': terms,
        'students': students,
        'selected_student_ids': selected_student_ids,
    })


@login_required
def promote_student(request, student_id, exam_id):
    if not (request.user.is_staff or request.user.is_superuser or user_is_staff(request.user)):
        messages.error(request, 'You do not have permission to promote students.')
        return redirect('home')

    student = get_object_or_404(Student, pk=student_id)
    classes = SchoolClasses.objects.exclude(pk=student.student_class_id).order_by('class_name') if student.student_class_id else SchoolClasses.objects.all().order_by('class_name')
    terms = Term.objects.filter(is_active=True).order_by('academic_year', 'name')

    if request.method == 'POST':
        target_class_id = request.POST.get('to_class')
        term_id = request.POST.get('term')
        remarks = (request.POST.get('remarks') or '').strip()

        if not target_class_id:
            messages.error(request, 'Please select a destination class.')
        else:
            target_class = get_object_or_404(SchoolClasses, pk=target_class_id)
            term = get_object_or_404(Term, pk=term_id) if term_id else (terms.first() if terms.exists() else None)
            if not term:
                messages.error(request, 'No active term is available for promotion.')
            elif student.student_class_id == target_class.id:
                messages.info(request, 'This student is already in the selected class.')
            else:
                current_class = student.student_class
                if current_class:
                    student.student_class = target_class
                    student.save(update_fields=['student_class'])
                    Promotion.objects.create(
                        student=student,
                        from_class=current_class,
                        to_class=target_class,
                        term=term,
                        remarks=remarks,
                        promoted_by=request.user
                    )
                    messages.success(request, f'{student.full_name()} was promoted to {target_class}.')
                else:
                    messages.error(request, 'The selected student does not currently belong to a class.')
        return redirect('promotions_list')

    return render(request, 'results/promote_student.html', {
        'student': student,
        'exam': None,
        'classes': classes,
        'terms': terms,
    })




# ==================== TEACHER RESULTS VIEWS ====================

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


@login_required
@login_required
def teacher_results_list(request):
    """Teachers view results for their classes"""
    if not user_is_staff(request.user):
        messages.error(request, 'You must be a teacher to access this page.')
        return redirect('home')

    try:
        teacher = request.user.teacher_profile
    except:
        messages.error(request, 'You must be a teacher to access this page.')
        return redirect('home')

    # Get classes assigned to this teacher
    from school_classes.models import ClassTeacher
    assigned_classes = ClassTeacher.objects.filter(
        teacher=teacher,
        is_active=True
    ).values_list('school_class_id', flat=True).distinct()

    # Get terms
    terms = Term.objects.filter(is_active=True).order_by('academic_year')

    context = {
        'assigned_classes': SchoolClasses.objects.filter(id__in=assigned_classes),
        'terms': terms,
    }

    return render(request, 'teachers/results/teacher_results_list.html', context)


@login_required
def teacher_class_results(request, class_id, term_id):
    """Teachers view results for a specific class"""
    try:
        teacher = request.user.teacher_profile
    except:
        messages.error(request, 'You must be a teacher to access this page.')
        return redirect('home')

    if not teacher_has_permission(teacher, 'view_results'):
        messages.error(request, 'You do not have permission to view results.')
        return redirect('home')

    school_class = get_object_or_404(SchoolClasses, pk=class_id)
    term = get_object_or_404(Term, pk=term_id)

    # Verify teacher is assigned to this class
    from school_classes.models import ClassTeacher
    if not ClassTeacher.objects.filter(teacher=teacher, school_class=school_class).exists():
        messages.error(request, 'You are not assigned to this class.')
        return redirect('teacher_results_list')

    # Get result template
    try:
        result_template = ResultTemplate.objects.get(
            school_class=school_class,
            term=term,
            is_active=True
        )
    except ResultTemplate.DoesNotExist:
        messages.error(request, f'No result template found for {school_class} - {term}')
        return redirect('teacher_results_list')

    # Get students in class
    students = Student.objects.filter(
        student_class=school_class,
        status='active'
    ).order_by('surname', 'other_names')

    # Get results for each student
    student_results = []
    for student in students:
        results = StudentResult.objects.filter(
            student=student,
            term=term,
            result_template=result_template
        ).select_related('class_subject__subject')

        term_result, created = TermResult.objects.get_or_create(
            student=student,
            term=term,
            result_template=result_template,
            defaults={'is_complete': False}
        )

        if results.exists() and not term_result.is_complete:
            term_result.calculate_aggregates()

        student_results.append({
            'student': student,
            'results': results,
            'term_result': term_result,
        })

    can_print_broadsheet = False
    broadsheet_url = None
    from school_classes.models import TeacherPermission
    if teacher_has_permission(teacher, 'print_broadsheet'):
        if ClassTeacher.objects.filter(teacher=teacher, school_class=school_class).exists():
            can_print_broadsheet = True
            broadsheet_url = reverse('teacher_print_broadsheet', args=[class_id, term_id])

    context = {
        'school_class': school_class,
        'term': term,
        'result_template': result_template,
        'student_results': student_results,
        'can_edit': True,  # Show bulk entry button if teacher is assigned to class
        'can_print': teacher_has_permission(teacher, 'print_results'),
        'can_print_broadsheet': can_print_broadsheet,
        'broadsheet_url': broadsheet_url,
    }

    return render(request, 'teachers/results/teacher_class_results.html', context)


@login_required
def teacher_edit_student_result(request, result_id):
    """Teachers edit student result scores with modern interface"""
    try:
        teacher = request.user.teacher_profile
    except:
        messages.error(request, 'You must be a teacher to access this page.')
        return redirect('home')

    if not teacher_has_permission(teacher, 'edit_results'):
        messages.error(request, 'You do not have permission to edit results.')
        return redirect('home')

    result = get_object_or_404(StudentResult, pk=result_id)

    # Verify teacher is assigned to this class
    from school_classes.models import ClassTeacher
    if not ClassTeacher.objects.filter(
        teacher=teacher,
        school_class=result.class_subject.school_class
    ).exists():
        messages.error(request, 'You are not authorized to edit this result.')
        return redirect('home')

    if request.method == 'POST':
        try:
            test_score = request.POST.get('test_score')
            exam_score = request.POST.get('exam_score')
            
            # Validate scores
            if test_score:
                test_score = float(test_score)
                if test_score < 0 or test_score > result.result_template.test_max_score:
                    messages.error(request, f'Test score must be between 0 and {result.result_template.test_max_score}')
                    return render(request, 'teachers/results/edit_student_result.html', get_result_context(result))
                result.test_score = test_score
            
            if exam_score:
                exam_score = float(exam_score)
                if exam_score < 0 or exam_score > result.result_template.exam_max_score:
                    messages.error(request, f'Exam score must be between 0 and {result.result_template.exam_max_score}')
                    return render(request, 'teachers/results/edit_student_result.html', get_result_context(result))
                result.exam_score = exam_score
            
            result.entered_by = request.user
            result.save()
            
            # Calculate aggregates for the individual result and mark term aggregates stale
            result.calculate_aggregates()
            TermResult.objects.filter(
                student=result.student,
                term=result.term,
                result_template=result.result_template
            ).update(is_complete=False, completed_at=None)

            messages.success(request, f'Result for {result.student.get_full_name} in {result.class_subject.subject.name} updated successfully.')
            return redirect('teacher_class_results', class_id=result.class_subject.school_class.id, term_id=result.term.id)
        
        except ValueError:
            messages.error(request, 'Invalid score value. Please enter numeric values.')
            return render(request, 'teachers/results/edit_student_result.html', get_result_context(result))
        except Exception as e:
            messages.error(request, f'Error saving result: {str(e)}')
            return render(request, 'teachers/results/edit_student_result.html', get_result_context(result))

    context = get_result_context(result)
    return render(request, 'teachers/results/edit_student_result.html', context)


def get_result_context(result):
    """Helper function to build result editing context"""
    return {
        'result': result,
        'student': result.student,
        'subject': result.class_subject.subject,
        'class': result.class_subject.school_class,
        'term': result.term,
        'template': result.result_template,
        'grade_scale': result.result_template.grade_scale,
        'max_test_score': float(result.result_template.test_max_score),
        'max_exam_score': float(result.result_template.exam_max_score),
        'test_weight': 100 * float(result.result_template.test_max_score) / (
            float(result.result_template.test_max_score) + float(result.result_template.exam_max_score)
        ),
        'exam_weight': 100 * float(result.result_template.exam_max_score) / (
            float(result.result_template.test_max_score) + float(result.result_template.exam_max_score)
        ),
    }


@login_required
def teacher_print_results(request, student_id, term_id):
    """Print student results (printable format)"""
    try:
        teacher = request.user.teacher_profile
    except:
        messages.error(request, 'You must be a teacher to access this page.')
        return redirect('home')

    if not teacher_has_permission(teacher, 'print_results'):
        messages.error(request, 'You do not have permission to print results.')
        return redirect('home')

    student = get_object_or_404(Student, pk=student_id)
    term = get_object_or_404(Term, pk=term_id)

    # Verify teacher is assigned to student's class
    from school_classes.models import ClassTeacher
    if not ClassTeacher.objects.filter(teacher=teacher, school_class=student.student_class).exists():
        messages.error(request, 'You are not authorized to print this result.')
        return redirect('home')

    # Get result template
    try:
        result_template = ResultTemplate.objects.get(
            school_class=student.student_class,
            term=term,
            is_active=True
        )
    except ResultTemplate.DoesNotExist:
        messages.error(request, 'No results available for this term.')
        return redirect('home')

    results = StudentResult.objects.filter(
        student=student,
        term=term,
        result_template=result_template
    ).select_related('class_subject__subject').order_by('class_subject__order')

    term_result, created = TermResult.objects.get_or_create(
        student=student,
        term=term,
        result_template=result_template,
        defaults={'is_complete': False}
    )

    if results.exists() and not term_result.is_complete:
        term_result.calculate_aggregates()

    context = {
        'student': student,
        'term': term,
        'result_template': result_template,
        'results': results,
        'term_result': term_result,
    }

    return render(request, 'teachers/results/print_results.html', context)


@login_required
def bulk_result_entry(request, class_id, term_id):
    """Bulk entry for class results with spreadsheet UI"""
    try:
        teacher = request.user.teacher_profile
    except:
        messages.error(request, 'You must be a teacher to access this page.')
        return redirect('home')

    school_class = get_object_or_404(SchoolClasses, pk=class_id)
    term = get_object_or_404(Term, pk=term_id)

    # Verify teacher is assigned to this class
    from school_classes.models import ClassTeacher
    if not ClassTeacher.objects.filter(teacher=teacher, school_class=school_class).exists():
        messages.error(request, 'You are not authorized to manage results for this class.')
        return redirect('home')

    # Get result template
    try:
        result_template = ResultTemplate.objects.get(
            school_class=school_class,
            term=term,
            is_active=True
        )
    except ResultTemplate.DoesNotExist:
        messages.error(request, f'No result template found for {school_class} - {term}')
        return redirect('teacher_results_list')

    # Get students and subjects
    students = Student.objects.filter(
        student_class=school_class,
        status='active'
    ).order_by('surname', 'other_names')

    class_subjects = ClassSubject.objects.filter(
        school_class=school_class
    ).select_related('subject').order_by('order')

    # Build results lookup: {student_id: {subject_id: result_obj}}
    results_by_student_subject = {student.id: {} for student in students}
    student_results = StudentResult.objects.filter(
        student__in=students,
        class_subject__in=class_subjects,
        term=term,
        result_template=result_template
    ).select_related('class_subject')

    for result in student_results:
        results_by_student_subject.setdefault(result.student_id, {})[result.class_subject_id] = result

    # Build conduct lookup: {student_id: conduct_obj}
    conduct_by_student = {
        conduct.student_id: conduct
        for conduct in StudentConduct.objects.filter(
            student__in=students,
            term=term
        )
    }
    for student in students:
        conduct_by_student.setdefault(student.id, None)

    if request.method == 'POST':
        # Process POST data and save results
        updated_student_ids = set()
        for student in students:
            for class_subject in class_subjects:
                test_field_name = f"test_{student.id}_{class_subject.id}"
                exam_field_name = f"exam_{student.id}_{class_subject.id}"

                test_score = request.POST.get(test_field_name, '').strip()
                exam_score = request.POST.get(exam_field_name, '').strip()

                # Convert to float if not empty
                try:
                    test_score = float(test_score) if test_score else None
                    exam_score = float(exam_score) if exam_score else None
                except ValueError:
                    continue

                if test_score is not None or exam_score is not None:
                    result, created = StudentResult.objects.get_or_create(
                        student=student,
                        class_subject=class_subject,
                        term=term,
                        result_template=result_template
                    )
                    
                    if test_score is not None:
                        result.test_score = test_score
                    if exam_score is not None:
                        result.exam_score = exam_score
                    
                    result.entered_by = request.user
                    result.save()
                    updated_student_ids.add(student.id)

            # Save conduct data for each student
            attendance = request.POST.get(f'attendance_{student.id}', '').strip()
            conduct = request.POST.get(f'conduct_{student.id}', '').strip()
            punctuality = request.POST.get(f'punctuality_{student.id}', '').strip()
            attentiveness = request.POST.get(f'attentiveness_{student.id}', '').strip()
            participation = request.POST.get(f'participation_{student.id}', '').strip()
            teacher_notes = request.POST.get(f'teacher_notes_{student.id}', '').strip()

            # Only save if at least one conduct field has data
            if any([attendance, conduct, punctuality, attentiveness, participation, teacher_notes]):
                student_conduct, created = StudentConduct.objects.get_or_create(
                    student=student,
                    term=term
                )
                
                if attendance:
                    student_conduct.attendance = attendance
                if conduct:
                    student_conduct.conduct = conduct
                if punctuality:
                    student_conduct.punctuality = punctuality
                if attentiveness:
                    student_conduct.attentiveness = attentiveness
                if participation:
                    student_conduct.participation = participation
                if teacher_notes:
                    student_conduct.teacher_notes = teacher_notes

                # Manual attendance override fields
                manual_att_pct = request.POST.get(f'manual_attendance_percentage_{student.id}', '').strip()
                manual_sessions_attended = request.POST.get(f'manual_attendance_sessions_attended_{student.id}', '').strip()
                manual_total_sessions = request.POST.get(f'manual_attendance_total_sessions_{student.id}', '').strip()
                manual_days_marked = request.POST.get(f'manual_attendance_days_marked_{student.id}', '').strip()
                manual_note = request.POST.get(f'manual_attendance_note_{student.id}', '').strip()

                if manual_att_pct != '':
                    try:
                        student_conduct.manual_attendance_percentage = float(manual_att_pct)
                    except ValueError:
                        pass
                if manual_sessions_attended != '':
                    try:
                        student_conduct.manual_attendance_sessions_attended = int(manual_sessions_attended)
                    except ValueError:
                        pass
                if manual_total_sessions != '':
                    try:
                        student_conduct.manual_attendance_total_sessions = int(manual_total_sessions)
                    except ValueError:
                        pass
                if manual_days_marked != '':
                    try:
                        student_conduct.manual_attendance_days_marked = int(manual_days_marked)
                    except ValueError:
                        pass
                if manual_note != '':
                    student_conduct.manual_attendance_note = manual_note
                
                student_conduct.entered_by = request.user
                student_conduct.save()

        if updated_student_ids:
            TermResult.objects.filter(
                student_id__in=updated_student_ids,
                term=term,
                result_template=result_template
            ).update(is_complete=False, completed_at=None)

        messages.success(request, f'✓ Results and conduct records saved successfully for {len(students)} students!')
        return redirect('teacher_class_results', class_id=class_id, term_id=term_id)

    context = {
        'school_class': school_class,
        'term': term,
        'result_template': result_template,
        'students': students,
        'class_subjects': class_subjects,
        'results_by_student_subject': results_by_student_subject,
        'conduct_by_student': conduct_by_student,
    }

    return render(request, 'results/bulk_result_entry.html', context)


@login_required
def teacher_print_broadsheet(request, class_id, term_id):
    """Print class broadsheet"""
    try:
        teacher = request.user.teacher_profile
    except:
        messages.error(request, 'You must be a teacher to access this page.')
        return redirect('home')

    if not teacher_has_permission(teacher, 'print_broadsheet'):
        messages.error(request, 'You do not have permission to print broadsheet.')
        return redirect('home')

    school_class = get_object_or_404(SchoolClasses, pk=class_id)
    term = get_object_or_404(Term, pk=term_id)

    # Verify teacher is assigned to this class
    from school_classes.models import ClassTeacher
    if not ClassTeacher.objects.filter(teacher=teacher, school_class=school_class).exists():
        messages.error(request, 'You are not assigned to this class.')
        return redirect('home')

    # Get result template
    try:
        result_template = ResultTemplate.objects.get(
            school_class=school_class,
            term=term,
            is_active=True
        )
    except ResultTemplate.DoesNotExist:
        messages.error(request, f'No result template found for {school_class} - {term}')
        return redirect('home')

    # Get all subjects
    class_subjects = ClassSubject.objects.filter(
        school_class=school_class
    ).select_related('subject').order_by('order')

    # Get all students
    students = Student.objects.filter(
        student_class=school_class,
        status='active'
    ).order_by('surname', 'other_names')

    # Build broadsheet data
    broadsheet_data = []
    for student in students:
        student_data = {
            'student': student,
            'subject_scores': {},
            'term_result': None,
        }

        for class_subject in class_subjects:
            try:
                result = StudentResult.objects.get(
                    student=student,
                    class_subject=class_subject,
                    term=term,
                    result_template=result_template
                )
                student_data['subject_scores'][class_subject.subject.name] = {
                    'test_score': result.test_score,
                    'exam_score': result.exam_score,
                    'total_score': result.total_score,
                    'grade': result.grade,
                }
            except StudentResult.DoesNotExist:
                student_data['subject_scores'][class_subject.subject.name] = None

        try:
            term_result = TermResult.objects.get(
                student=student,
                term=term,
                result_template=result_template
            )
            if not term_result.is_complete:
                term_result.calculate_aggregates()
            student_data['term_result'] = term_result
        except TermResult.DoesNotExist:
            pass

        broadsheet_data.append(student_data)

    context = {
        'school_class': school_class,
        'term': term,
        'result_template': result_template,
        'class_subjects': class_subjects,
        'broadsheet_data': broadsheet_data,
    }

    return render(request, 'teachers/results/print_broadsheet.html', context)


# ==================== TEACHER: REPORT CARD COMMENTS ====================

@login_required
def teacher_edit_report_card(request, student_id, term_id):
    """Teachers edit/add comments to student report cards"""
    try:
        teacher = request.user.teacher_profile
    except:
        messages.error(request, 'You must be a teacher to access this page.')
        return redirect('home')

    if not teacher_has_permission(teacher, 'edit_results'):
        messages.error(request, 'You do not have permission to edit report cards.')
        return redirect('home')

    student = get_object_or_404(Student, pk=student_id)
    term = get_object_or_404(Term, pk=term_id)

    # Verify teacher is assigned to student's class
    from school_classes.models import ClassTeacher
    if not ClassTeacher.objects.filter(teacher=teacher, school_class=student.student_class).exists():
        messages.error(request, 'You are not authorized to edit this report card.')
        return redirect('home')

    # Get result template
    try:
        result_template = ResultTemplate.objects.get(
            school_class=student.student_class,
            term=term,
            is_active=True
        )
    except ResultTemplate.DoesNotExist:
        messages.error(request, 'No results available for this term.')
        return redirect('home')

    # Get or create term result
    term_result, created = TermResult.objects.get_or_create(
        student=student,
        term=term,
        result_template=result_template,
        defaults={'is_complete': False}
    )

    # Get existing comment or create new form
    report_comment = ReportCardComment.objects.filter(
        term_result=term_result,
        teacher=teacher
    ).first()

    # Get student results for display
    results = StudentResult.objects.filter(
        student=student,
        term=term,
        result_template=result_template
    ).select_related('class_subject__subject').order_by('class_subject__order')

    from .forms import ReportCardCommentForm

    if request.method == 'POST':
        form = ReportCardCommentForm(request.POST, instance=report_comment)
        score_errors = []
        saved_subjects = []
        results_updated = False

        for result in results:
            test_score_raw = request.POST.get(f'test_{result.id}', '').strip()
            exam_score_raw = request.POST.get(f'exam_{result.id}', '').strip()
            result_changed = False

            if test_score_raw != '':
                try:
                    test_score = float(test_score_raw)
                except ValueError:
                    score_errors.append(f'Invalid test score for {result.class_subject.subject.name}.')
                else:
                    if test_score < 0 or test_score > result.result_template.test_max_score:
                        score_errors.append(
                            f'Test score for {result.class_subject.subject.name} must be between 0 and {result.result_template.test_max_score}.'
                        )
                    else:
                        result.test_score = test_score
                        result_changed = True

            if exam_score_raw != '':
                try:
                    exam_score = float(exam_score_raw)
                except ValueError:
                    score_errors.append(f'Invalid exam score for {result.class_subject.subject.name}.')
                else:
                    if exam_score < 0 or exam_score > result.result_template.exam_max_score:
                        score_errors.append(
                            f'Exam score for {result.class_subject.subject.name} must be between 0 and {result.result_template.exam_max_score}.'
                        )
                    else:
                        result.exam_score = exam_score
                        result_changed = True

            if result_changed:
                result.entered_by = request.user
                result.save()
                saved_subjects.append(result.class_subject.subject.name)
                results_updated = True

        if score_errors:
            for error in score_errors:
                messages.error(request, error)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.term_result = term_result
            comment.teacher = teacher
            comment.created_by = request.user
            if comment.comment or report_comment:
                comment.save()
        else:
            messages.error(request, 'Please correct the comment form errors below.')

        if results_updated and not score_errors:
            TermResult.objects.filter(
                student=student,
                term=term,
                result_template=result_template
            ).update(is_complete=False, completed_at=None)
            if saved_subjects:
                subject_list = ', '.join(saved_subjects)
                messages.success(request, f'Saved scores for: {subject_list}.')
            else:
                messages.success(request, 'Report card updated successfully.')
            return redirect('teacher_class_results', class_id=student.student_class.id, term_id=term.id)

        if not results_updated and (not form.is_valid() or not form.cleaned_data.get('comment', '').strip()):
            messages.info(request, 'No changes detected to save.')
    else:
        form = ReportCardCommentForm(instance=report_comment)

    # Get student conduct data
    student_conduct = StudentConduct.objects.filter(
        student=student,
        term=term
    ).first()

    context = {
        'student': student,
        'term': term,
        'term_result': term_result,
        'results': results,
        'form': form,
        'comment': report_comment,
        'student_conduct': student_conduct,
    }

    return render(request, 'teachers/results/edit_report_card.html', context)


@login_required
def teacher_view_report_card_comments(request, student_id, term_id):
    """Teachers view all comments on a student's report card"""
    try:
        teacher = request.user.teacher_profile
    except:
        messages.error(request, 'You must be a teacher to access this page.')
        return redirect('home')

    student = get_object_or_404(Student, pk=student_id)
    term = get_object_or_404(Term, pk=term_id)

    # Verify teacher is assigned to student's class
    from school_classes.models import ClassTeacher
    if not ClassTeacher.objects.filter(teacher=teacher, school_class=student.student_class).exists():
        messages.error(request, 'You are not authorized to view this report card.')
        return redirect('home')

    # Get result template
    try:
        result_template = ResultTemplate.objects.get(
            school_class=student.student_class,
            term=term,
            is_active=True
        )
    except ResultTemplate.DoesNotExist:
        messages.error(request, 'No results available for this term.')
        return redirect('home')

    # Get term result and comments
    term_result, created = TermResult.objects.get_or_create(
        student=student,
        term=term,
        result_template=result_template,
        defaults={'is_complete': False}
    )

    comments = ReportCardComment.objects.filter(term_result=term_result)

    context = {
        'student': student,
        'term': term,
        'term_result': term_result,
        'comments': comments,
    }

    return render(request, 'teachers/results/report_card_comments.html', context)


# ==================== ADMIN: RESULT PUBLICATION ====================

def admin_is_staff(user):
    """Check if user is admin/staff"""
    try:
        return user.is_staff or user.groups.filter(name__in=['Admin', 'Staff']).exists()
    except:
        return False


@login_required
def publish_result(request, result_id):
    """Admin publishes a single result so student can see it"""
    if not admin_is_staff(request.user):
        messages.error(request, 'You do not have permission to publish results.')
        return redirect('home')
    
    result = get_object_or_404(StudentResult, pk=result_id)
    result.is_published = True
    from django.utils import timezone
    result.published_at = timezone.now()
    result.published_by = request.user
    result.save()
    
    messages.success(request, f'Result for {result.student.full_name()} - {result.class_subject.subject.name} published.')
    return redirect('results_home')


@login_required
def unpublish_result(request, result_id):
    """Admin unpublishes a result so student cannot see it"""
    if not admin_is_staff(request.user):
        messages.error(request, 'You do not have permission to unpublish results.')
        return redirect('home')
    
    result = get_object_or_404(StudentResult, pk=result_id)
    result.is_published = False
    result.published_at = None
    result.published_by = None
    result.save()
    
    messages.success(request, f'Result for {result.student.full_name()} - {result.class_subject.subject.name} unpublished.')
    return redirect('results_home')


@login_required
def publish_class_results(request, class_id, term_id):
    """Admin publishes all results for a class and term"""
    if not admin_is_staff(request.user):
        messages.error(request, 'You do not have permission to publish results.')
        return redirect('home')
    
    school_class = get_object_or_404(SchoolClasses, pk=class_id)
    term = get_object_or_404(Term, pk=term_id)
    
    # Get all unpublished results for this class and term
    results = StudentResult.objects.filter(
        student__student_class=school_class,
        term=term,
        is_published=False
    )
    
    count = results.count()
    
    if request.method == 'POST':
        from django.utils import timezone
        results.update(
            is_published=True,
            published_at=timezone.now(),
            published_by=request.user
        )
        messages.success(request, f'Published {count} results for {school_class} - {term}.')
        return redirect('results_home')
    
    context = {
        'school_class': school_class,
        'term': term,
        'result_count': count,
    }
    
    return render(request, 'results/admin/confirm_publish_results.html', context)


@login_required
def unpublish_class_results(request, class_id, term_id):
    """Admin unpublishes all results for a class and term"""
    if not admin_is_staff(request.user):
        messages.error(request, 'You do not have permission to unpublish results.')
        return redirect('home')
    
    school_class = get_object_or_404(SchoolClasses, pk=class_id)
    term = get_object_or_404(Term, pk=term_id)
    
    # Get all published results for this class and term
    results = StudentResult.objects.filter(
        student__student_class=school_class,
        term=term,
        is_published=True
    )
    
    count = results.count()
    
    if request.method == 'POST':
        results.update(
            is_published=False,
            published_at=None,
            published_by=None
        )
        messages.success(request, f'Unpublished {count} results for {school_class} - {term}.')
        return redirect('results_home')
    
    context = {
        'school_class': school_class,
        'term': term,
        'result_count': count,
    }
    
    return render(request, 'results/admin/confirm_unpublish_results.html', context)

