from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden, JsonResponse
from datetime import date
from django.db.models import Count, Q
from django.utils.decorators import method_decorator
from .models import AttendanceRecord, AttendanceSession, AttendanceHoliday, AttendanceSettings
from .forms import AttendanceRecordForm
from students.models import Student
from school_classes.models import SchoolClasses, ClassTeacher, Teacher
from exams.models import Term


def get_attendance_settings():
    """Get or create attendance settings"""
    settings, created = AttendanceSettings.objects.get_or_create(pk=1)
    return settings


def is_holiday(check_date):
    """Check if a given date is a holiday"""
    return AttendanceHoliday.objects.filter(
        is_active=True,
        start_date__lte=check_date,
        end_date__gte=check_date
    ).exists()


def get_holiday_for_date(check_date):
    """Get holiday record for a given date"""
    return AttendanceHoliday.objects.filter(
        is_active=True,
        start_date__lte=check_date,
        end_date__gte=check_date
    ).first()


def user_profile_approved(user):
    """Defensively check if user profile is approved"""
    try:
        return user.profile.is_approved
    except AttributeError:
        return False


def user_is_staff(user):
    """Defensively check if user is staff"""
    try:
        return (
            user.profile.is_approved and
            user.groups.filter(name__in=['Teacher', 'Staff']).exists()
        )
    except AttributeError:
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


def get_term_for_date(attendance_date):
    """Return the configured term for the given date, if any."""
    return Term.objects.filter(
        start_date__isnull=False,
        end_date__isnull=False,
        start_date__lte=attendance_date,
        end_date__gte=attendance_date
    ).first()


def attendance_terms_configured():
    return Term.objects.filter(
        is_active=True,
        start_date__isnull=False,
        end_date__isnull=False
    ).exists()


class AttendanceRecordListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = AttendanceRecord
    template_name = 'attendance/attendance_list.html'
    context_object_name = 'attendance_records'
    paginate_by = 20
    ordering = ['-date', 'student']

    def test_func(self):
        return user_profile_approved(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = user_is_staff(self.request.user)
        return context


class AttendanceRecordDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = AttendanceRecord
    template_name = 'attendance/attendance_detail.html'
    context_object_name = 'attendance_record'

    def test_func(self):
        return user_profile_approved(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = user_is_staff(self.request.user)
        return context


class AttendanceRecordCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = AttendanceRecord
    form_class = AttendanceRecordForm
    template_name = 'attendance/attendance_form.html'
    success_url = reverse_lazy('attendance_list')

    def test_func(self):
        return user_is_staff(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Attendance record created successfully.')
        return super().form_valid(form)


class AttendanceRecordUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = AttendanceRecord
    form_class = AttendanceRecordForm
    template_name = 'attendance/attendance_form.html'
    success_url = reverse_lazy('attendance_list')

    def test_func(self):
        return user_is_staff(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Attendance record updated successfully.')
        return super().form_valid(form)


class AttendanceRecordDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = AttendanceRecord
    template_name = 'attendance/attendance_confirm_delete.html'
    success_url = reverse_lazy('attendance_list')

    def test_func(self):
        return user_is_staff(self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Attendance record deleted successfully.')
        return super().delete(request, *args, **kwargs)


# ==================== TEACHER ATTENDANCE VIEWS ====================

@method_decorator(login_required, name='dispatch')
class TeacherAttendanceMarkView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Teachers mark attendance for their class"""
    template_name = 'teachers/attendance/mark_attendance.html'

    def test_func(self):
        try:
            teacher = self.request.user.teacher_profile
            return teacher_has_permission(teacher, 'mark_attendance')
        except:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.request.user.teacher_profile

        # Get classes assigned to teacher
        assigned_classes = ClassTeacher.objects.filter(
            teacher=teacher,
            is_active=True
        ).values_list('school_class_id', flat=True).distinct()

        context['classes'] = SchoolClasses.objects.filter(id__in=assigned_classes)

        # Determine date to mark attendance for
        selected_date_str = self.request.GET.get('date')
        if selected_date_str:
            try:
                selected_date = date.fromisoformat(selected_date_str)
            except ValueError:
                selected_date = date.today()
        else:
            selected_date = date.today()

        context['selected_date'] = selected_date
        context['selected_term'] = get_term_for_date(selected_date)
        context['term_date_restriction_enabled'] = attendance_terms_configured()
        context['attendance_settings'] = get_attendance_settings()
        
        # Check for holidays
        holiday = get_holiday_for_date(selected_date)
        context['holiday'] = holiday
        context['is_holiday'] = holiday is not None
        context['date_allowed'] = True

        if context['term_date_restriction_enabled'] and not context['selected_term']:
            context['date_allowed'] = False
            context['term_date_message'] = (
                'Attendance can only be marked within configured term resumption and closing dates.'
            )

        # Get class if specified
        class_id = self.request.GET.get('class_id')
        if class_id:
            try:
                school_class = SchoolClasses.objects.get(id=class_id)
                if school_class.id in assigned_classes:
                    context['selected_class'] = school_class
                    context['students'] = Student.objects.filter(
                        student_class=school_class,
                        status='active'
                    ).order_by('surname', 'other_names')
                    active_records = AttendanceRecord.objects.filter(
                        school_class=school_class,
                        date=selected_date
                    )
                    attendance_map = {record.student_id: record for record in active_records}
                    
                    # Attach attendance record directly to each student for easier template access
                    for student in context['students']:
                        student.attendance_record = attendance_map.get(student.id)
                    
                    context['attendance_map'] = attendance_map
                    context['selected_session'] = AttendanceSession.objects.filter(
                        school_class=school_class,
                        date=selected_date
                    ).first()
                    context['day_type'] = (
                        context['selected_session'].day_type if context['selected_session'] else 'school_day'
                    )
            except SchoolClasses.DoesNotExist:
                pass

        return context

    def post(self, request, *args, **kwargs):
        teacher = request.user.teacher_profile
        class_id = request.POST.get('class_id')

        try:
            school_class = SchoolClasses.objects.get(id=class_id)

            # Verify teacher is assigned
            if not ClassTeacher.objects.filter(teacher=teacher, school_class=school_class).exists():
                messages.error(request, 'You are not assigned to this class.')
                return redirect('teacher_mark_attendance')

            attendance_date_str = request.POST.get('date')
            try:
                attendance_date = date.fromisoformat(attendance_date_str) if attendance_date_str else date.today()
            except ValueError:
                attendance_date = date.today()

            selected_term = get_term_for_date(attendance_date)
            if attendance_terms_configured() and not selected_term:
                messages.error(request, 'Attendance can only be marked on dates inside configured term resumption and closing dates.')
                return redirect('teacher_mark_attendance')

            day_type = request.POST.get('day_type', 'school_day')
            students = Student.objects.filter(student_class=school_class, status='active')
            present_count = 0
            absent_count = 0

            if day_type != 'school_day':
                # Mark the day as a holiday/break for this class and remove any attendance records
                AttendanceRecord.objects.filter(school_class=school_class, date=attendance_date).delete()
                total_students = len(students)
                session, created = AttendanceSession.objects.update_or_create(
                    school_class=school_class,
                    date=attendance_date,
                    defaults={
                        'teacher': teacher,
                        'total_students': total_students,
                        'present_count': 0,
                        'absent_count': 0,
                        'day_type': day_type,
                    }
                )
                messages.success(request, f'{session.get_day_type_display()} recorded for {school_class} on {attendance_date}.')
                return redirect('teacher_mark_attendance')

            # Process attendance for each student on a school day
            for student in students:
                # Check if attendance record already exists
                try:
                    attendance = AttendanceRecord.objects.get(
                        student=student,
                        date=attendance_date,
                        school_class=school_class
                    )
                    # Record exists - only update fields that are explicitly being set
                    # Preserve fields that weren't explicitly changed
                    morning_field = f'student_{student.id}_morning'
                    afternoon_field = f'student_{student.id}_afternoon'
                    
                    if morning_field in request.POST:
                        attendance.morning_present = request.POST.get(morning_field) == 'on'
                    
                    if afternoon_field in request.POST:
                        attendance.afternoon_present = request.POST.get(afternoon_field) == 'on'
                    
                    # Update notes and marked_by
                    attendance.notes = request.POST.get(f'notes_{student.id}', '')
                    attendance.marked_by = request.user
                    attendance.save()
                    
                except AttendanceRecord.DoesNotExist:
                    # New record - create with provided values
                    morning_present = request.POST.get(f'student_{student.id}_morning') == 'on'
                    afternoon_present = request.POST.get(f'student_{student.id}_afternoon') == 'on'
                    notes = request.POST.get(f'notes_{student.id}', '')
                    
                    attendance = AttendanceRecord.objects.create(
                        student=student,
                        date=attendance_date,
                        school_class=school_class,
                        morning_present=morning_present,
                        afternoon_present=afternoon_present,
                        marked_by=request.user,
                        notes=notes
                    )

                if attendance.present:
                    present_count += 1
                else:
                    absent_count += 1

            session, created = AttendanceSession.objects.update_or_create(
                school_class=school_class,
                date=attendance_date,
                defaults={
                    'teacher': teacher,
                    'total_students': len(students),
                    'present_count': present_count,
                    'absent_count': absent_count,
                    'day_type': 'school_day',
                }
            )

            messages.success(request, f'Attendance marked for {school_class}. Present: {present_count}, Absent: {absent_count}')
            return redirect('teacher_mark_attendance')

        except SchoolClasses.DoesNotExist:
            messages.error(request, 'Class not found.')
            return redirect('teacher_mark_attendance')


@method_decorator(login_required, name='dispatch')
class TeacherAttendanceListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Teachers view attendance records for their classes"""
    template_name = 'teachers/attendance/attendance_list.html'
    context_object_name = 'attendance_records'
    paginate_by = 30

    def test_func(self):
        try:
            teacher = self.request.user.teacher_profile
            return teacher_has_permission(teacher, 'view_attendance')
        except:
            return False

    def get_queryset(self):
        teacher = self.request.user.teacher_profile

        # Get classes assigned to teacher
        assigned_classes = ClassTeacher.objects.filter(
            teacher=teacher,
            is_active=True
        ).values_list('school_class_id', flat=True)

        queryset = AttendanceRecord.objects.filter(
            school_class_id__in=assigned_classes
        ).select_related('student', 'school_class', 'marked_by')

        # Filter by class if specified
        class_id = self.request.GET.get('class_id')
        if class_id:
            queryset = queryset.filter(school_class_id=class_id)

        # Filter by student if specified
        student_id = self.request.GET.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        return queryset.order_by('-date', 'student')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.request.user.teacher_profile

        # Get assigned classes
        assigned_classes = ClassTeacher.objects.filter(
            teacher=teacher,
            is_active=True
        ).values_list('school_class_id', flat=True).distinct()

        context['classes'] = SchoolClasses.objects.filter(id__in=assigned_classes)
        context['selected_class'] = self.request.GET.get('class_id')
        context['show_attendance_report'] = self.request.user.is_superuser or user_is_staff(self.request.user)

        return context


@method_decorator(login_required, name='dispatch')
class TeacherAttendanceReportView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Teachers view attendance reports for their classes"""
    template_name = 'teachers/attendance/attendance_report.html'

    def test_func(self):
        try:
            teacher = self.request.user.teacher_profile
            return teacher_has_permission(teacher, 'view_attendance')
        except:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.request.user.teacher_profile

        # Get assigned classes
        assigned_classes = ClassTeacher.objects.filter(
            teacher=teacher,
            is_active=True
        ).values_list('school_class_id', flat=True).distinct()

        classes = SchoolClasses.objects.filter(id__in=assigned_classes)
        context['classes'] = classes

        # Get class if specified
        class_id = self.request.GET.get('class_id')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        context['selected_class_id'] = class_id
        context['start_date'] = start_date
        context['end_date'] = end_date

        if class_id:
            try:
                school_class = SchoolClasses.objects.get(id=class_id, id__in=assigned_classes)
                context['selected_class'] = school_class

                # Get all students in class
                students = Student.objects.filter(
                    student_class=school_class,
                    status='active'
                ).order_by('surname', 'other_names')

                # Calculate attendance stats for each student
                student_stats = []
                for student in students:
                    records = AttendanceRecord.objects.filter(
                        student=student,
                        school_class=school_class
                    )

                    total_records = records.count()
                    present_days = records.filter(present=True).count()
                    present_sessions = sum(int(record.morning_present) + int(record.afternoon_present) for record in records)
                    total_half_sessions = total_records * 2
                    absent_sessions = total_half_sessions - present_sessions
                    days_marked = records.values('date').distinct().count()
                    attendance_percentage = (present_sessions / total_half_sessions * 100) if total_half_sessions > 0 else 0

                    student_stats.append({
                        'student': student,
                        'total_records': total_records,
                        'present_days': present_days,
                        'present_sessions': present_sessions,
                        'absent_sessions': absent_sessions,
                        'days_marked': days_marked,
                        'attendance_percentage': round(attendance_percentage, 2)
                    })

                context['student_stats'] = student_stats

                # Generate per-day class attendance report data
                attendance_filters = {'school_class': school_class}
                if start_date:
                    attendance_filters['date__gte'] = start_date
                if end_date:
                    attendance_filters['date__lte'] = end_date

                attendance_records = AttendanceRecord.objects.filter(**attendance_filters)
                report_data = []
                for date_info in attendance_records.values('date').distinct().order_by('date'):
                    day = date_info['date']
                    day_records = attendance_records.filter(date=day)
                    total_students = day_records.count()
                    present_sessions = sum(record.present_sessions for record in day_records)
                    absent_sessions = total_students * 2 - present_sessions
                    report_data.append({
                        'date': day,
                        'class_name': str(school_class),
                        'total': total_students,
                        'present': present_sessions,
                        'absent': absent_sessions,
                        'late': 0,
                        'percentage': round((present_sessions / (total_students * 2) * 100) if total_students > 0 else 0, 2)
                    })

                context['report_data'] = report_data

            except SchoolClasses.DoesNotExist:
                pass

        return context


@method_decorator(login_required, name='dispatch')
class AttendanceReportView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Staff/admin class attendance report"""
    template_name = 'teachers/attendance/attendance_report.html'

    def test_func(self):
        return user_is_staff(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        class_id = self.request.GET.get('class_id')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        classes = SchoolClasses.objects.all().order_by('class_name')
        context['classes'] = classes
        context['report_title'] = 'Class Attendance Statistics'
        context['selected_class_id'] = class_id
        context['start_date'] = start_date
        context['end_date'] = end_date

        if class_id:
            try:
                school_class = classes.get(pk=class_id)
                context['selected_class'] = school_class

                attendance_records = AttendanceRecord.objects.filter(school_class=school_class)
                if start_date:
                    attendance_records = attendance_records.filter(date__gte=start_date)
                if end_date:
                    attendance_records = attendance_records.filter(date__lte=end_date)

                report_data = []
                for date_info in attendance_records.values('date').distinct().order_by('date'):
                    day = date_info['date']
                    day_records = attendance_records.filter(date=day)
                    total_students = day_records.count()
                    present_sessions = sum(record.present_sessions for record in day_records)
                    absent_sessions = total_students * 2 - present_sessions
                    report_data.append({
                        'date': day,
                        'class_name': str(school_class),
                        'total': total_students,
                        'present': present_sessions,
                        'absent': absent_sessions,
                        'late': 0,
                        'percentage': round((present_sessions / (total_students * 2) * 100) if total_students > 0 else 0, 2)
                    })

                context['report_data'] = report_data
            except SchoolClasses.DoesNotExist:
                pass

        return context


@method_decorator(login_required, name='dispatch')
class StudentAttendanceHistoryView(LoginRequiredMixin, TemplateView):
    """Students view their own attendance history"""
    template_name = 'students/attendance_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the student
        try:
            student = Student.objects.get(user=self.request.user)
            context['student'] = student
            
            # Get all attendance records for this student
            attendance_records = AttendanceRecord.objects.filter(
                student=student
            ).select_related('school_class', 'marked_by').order_by('-date')
            
            context['attendance_records'] = attendance_records
            
            # Calculate statistics
            total_records = attendance_records.count()
            present_count = attendance_records.filter(present=True).count()
            absent_count = total_records - present_count
            total_half_sessions = total_records * 2
            present_sessions = sum(int(record.morning_present) + int(record.afternoon_present) for record in attendance_records)
            absent_sessions = total_half_sessions - present_sessions
            attendance_percentage = (present_sessions / total_half_sessions * 100) if total_half_sessions > 0 else 0
            days_marked = attendance_records.values('date').distinct().count()

            weekly_summary = {}
            for record in attendance_records:
                week_no = record.date.isocalendar()[1]
                week_stat = weekly_summary.setdefault(week_no, {
                    'week': week_no,
                    'present_sessions': 0,
                    'absent_sessions': 0,
                    'days': set(),
                })
                week_stat['present_sessions'] += int(record.morning_present) + int(record.afternoon_present)
                week_stat['absent_sessions'] += 2 - (int(record.morning_present) + int(record.afternoon_present))
                week_stat['days'].add(record.date)

            weekly_stats = []
            for week in sorted(weekly_summary):
                stats = weekly_summary[week]
                days_count = len(stats['days'])
                weekly_stats.append({
                    'week': week,
                    'present_sessions': stats['present_sessions'],
                    'absent_sessions': stats['absent_sessions'],
                    'days_marked': days_count,
                    'attendance_percentage': round((stats['present_sessions'] / (days_count * 2) * 100), 2) if days_count > 0 else 0,
                })

            context['total_records'] = total_records
            context['present_count'] = present_count
            context['absent_count'] = absent_count
            context['total_half_sessions'] = total_half_sessions
            context['present_sessions'] = present_sessions
            context['absent_sessions'] = absent_sessions
            context['days_marked'] = days_marked
            context['attendance_percentage'] = round(attendance_percentage, 2)
            context['weekly_stats'] = weekly_stats
            
            # Get stats by class
            classes = student.school_class
            if classes:
                class_records = attendance_records.filter(school_class=classes)
                context['class_total'] = class_records.count()
                context['class_present'] = class_records.filter(present=True).count()
                class_percentage = (context['class_present'] / context['class_total'] * 100) if context['class_total'] > 0 else 0
                context['class_percentage'] = round(class_percentage, 2)
            
        except Student.DoesNotExist:
            context['error'] = 'Student profile not found.'
            
        return context


from .forms import AttendanceRecordForm, AttendanceSettingsForm
from django.http import JsonResponse, HttpResponseForbidden


class AttendanceSettingsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Display and manage attendance settings"""
    template_name = 'attendance/attendance_settings.html'
    
    def test_func(self):
        """Only staff/admin can view"""
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        settings_instance, created = AttendanceSettings.objects.get_or_create(pk=1)
        context['settings'] = settings_instance
        context['form'] = AttendanceSettingsForm(instance=settings_instance)
        
        # Get all active and inactive holidays
        context['holidays'] = AttendanceHoliday.objects.all().order_by('-start_date')
        context['active_holidays'] = AttendanceHoliday.objects.filter(is_active=True).count()
        context['inactive_holidays'] = AttendanceHoliday.objects.filter(is_active=False).count()
        
        # Calculate upcoming holidays (from today onwards)
        from django.utils import timezone
        today = timezone.now().date()
        context['upcoming_holidays'] = AttendanceHoliday.objects.filter(
            is_active=True,
            start_date__gte=today
        ).order_by('start_date')
        
        # Calculate ongoing holidays (currently active)
        context['ongoing_holidays'] = AttendanceHoliday.objects.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        ).order_by('start_date')
        
        return context

    def post(self, request, *args, **kwargs):
        settings_instance, created = AttendanceSettings.objects.get_or_create(pk=1)
        form = AttendanceSettingsForm(request.POST, instance=settings_instance)
        if form.is_valid():
            settings_obj = form.save(commit=False)
            settings_obj.last_updated_by = request.user
            settings_obj.save()
            messages.success(request, 'Attendance settings were saved successfully.')
            return redirect('attendance_settings')

        context = self.get_context_data(**kwargs)
        context['form'] = form
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class AdminStudentAttendanceView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin page to manage student attendance settings and populate class stats"""
    template_name = 'attendance/admin_student_settings.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from school_classes.models import SchoolClasses
        from django.utils import timezone
        classes = SchoolClasses.objects.all().order_by('class_name')
        context['classes'] = classes

        class_id = (self.request.GET.get('class_id') or '').strip()
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        populate = self.request.GET.get('populate')

        context['selected_class_id'] = class_id
        context['start_date'] = start_date
        context['end_date'] = end_date

        # If a class is selected, provide its active students for optional per-student lookup
        if class_id and class_id != 'all':
            try:
                from students.models import Student
                school_class = SchoolClasses.objects.get(pk=class_id)
                students_in_class = Student.objects.filter(student_class=school_class, status='active').order_by('surname', 'other_names')
                context['students_in_class'] = students_in_class
            except (SchoolClasses.DoesNotExist, ValueError):
                context['students_in_class'] = []

        # If populate requested, compute stats for selected class or all classes
        if populate:
            from students.models import Student
            from .models import AttendanceRecord

            target_classes = classes if not class_id or class_id == 'all' else classes.filter(pk=class_id)
            stats = []
            for school_class in target_classes:
                students = Student.objects.filter(student_class=school_class, status='active')
                class_records = AttendanceRecord.objects.filter(school_class=school_class)
                if start_date:
                    class_records = class_records.filter(date__gte=start_date)
                if end_date:
                    class_records = class_records.filter(date__lte=end_date)

                total_days = class_records.values('date').distinct().count()
                total_students = students.count()
                total_half_sessions = total_days * total_students * 2 if total_days and total_students else 0
                present_sessions = sum(r.present_sessions for r in class_records) if class_records.exists() else 0

                percentage = round((present_sessions / total_half_sessions * 100), 2) if total_half_sessions else 0

                stats.append({
                    'class': school_class,
                    'total_days': total_days,
                    'total_students': total_students,
                    'present_sessions': present_sessions,
                    'attendance_percentage': percentage,
                })

            context['stats'] = stats

        # If a specific student was requested, compute individual stats
        student_id = (self.request.GET.get('student_id') or '').strip()
        context['selected_student_id'] = student_id
        if student_id:
            try:
                from students.models import Student
                from .models import AttendanceRecord
                if class_id and class_id != 'all':
                    student = Student.objects.filter(pk=student_id, student_class__pk=class_id).first()
                    if not student:
                        raise Student.DoesNotExist
                else:
                    student = Student.objects.get(pk=student_id)

                student_records = AttendanceRecord.objects.filter(student=student)
                if start_date:
                    student_records = student_records.filter(date__gte=start_date)
                if end_date:
                    student_records = student_records.filter(date__lte=end_date)

                total_records = student_records.count()
                present_count = student_records.filter(present=True).count()
                total_half_sessions = total_records * 2
                present_sessions = sum(int(r.morning_present) + int(r.afternoon_present) for r in student_records)
                absent_sessions = total_half_sessions - present_sessions
                attendance_percentage = (present_sessions / total_half_sessions * 100) if total_half_sessions > 0 else 0
                days_marked = student_records.values('date').distinct().count()

                # weekly breakdown
                weekly_summary = {}
                for record in student_records:
                    week_no = record.date.isocalendar()[1]
                    week_stat = weekly_summary.setdefault(week_no, {'week': week_no, 'present_sessions': 0, 'absent_sessions': 0, 'days': set()})
                    week_stat['present_sessions'] += int(record.morning_present) + int(record.afternoon_present)
                    week_stat['absent_sessions'] += 2 - (int(record.morning_present) + int(record.afternoon_present))
                    week_stat['days'].add(record.date)

                weekly_stats = []
                for week in sorted(weekly_summary):
                    stats_w = weekly_summary[week]
                    days_count = len(stats_w['days'])
                    weekly_stats.append({
                        'week': week,
                        'present_sessions': stats_w['present_sessions'],
                        'absent_sessions': stats_w['absent_sessions'],
                        'days_marked': days_count,
                        'attendance_percentage': round((stats_w['present_sessions'] / (days_count * 2) * 100), 2) if days_count > 0 else 0,
                    })

                context['student'] = student
                context['student_total_records'] = total_records
                context['student_present_count'] = present_count
                context['student_total_half_sessions'] = total_half_sessions
                context['student_present_sessions'] = present_sessions
                context['student_absent_sessions'] = absent_sessions
                context['student_days_marked'] = days_marked
                context['student_attendance_percentage'] = round(attendance_percentage, 2)
                context['student_weekly_stats'] = weekly_stats

            except Student.DoesNotExist:
                context['student_error'] = 'Student not found for the given ID or selected class.'

        return context


def students_by_class(request):
    """Return JSON list of active students for a given class id. GET param: class_id"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseForbidden('Forbidden')

    class_id = request.GET.get('class_id')
    if not class_id:
        return JsonResponse({'students': []})

    try:
        from students.models import Student
        students = Student.objects.filter(student_class__pk=class_id, status='active').order_by('first_name', 'last_name')
        data = [{'id': s.pk, 'name': (s.get_full_name() if hasattr(s, 'get_full_name') else str(s))} for s in students]
        return JsonResponse({'students': data})
    except Exception as e:
        return JsonResponse({'students': [], 'error': str(e)})


def classes_list(request):
    """Return JSON list of classes (id and name)."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseForbidden('Forbidden')
    try:
        from school_classes.models import SchoolClasses
        classes = SchoolClasses.objects.all().order_by('class_name')
        data = [{'id': c.pk, 'name': str(c)} for c in classes]
        return JsonResponse({'classes': data})
    except Exception:
        return JsonResponse({'classes': [], 'error': 'Could not load classes'})
