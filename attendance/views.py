from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Count, Q
from django.utils.decorators import method_decorator
from .models import AttendanceRecord, AttendanceSession
from .forms import AttendanceRecordForm
from students.models import Student
from school_classes.models import SchoolClasses, ClassTeacher, Teacher


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
            except SchoolClasses.DoesNotExist:
                pass

        return context

    def post(self, request, *args, **kwargs):
        teacher = request.user.teacher_profile
        class_id = request.POST.get('class_id')
        from django.utils import timezone
        from datetime import date

        try:
            school_class = SchoolClasses.objects.get(id=class_id)

            # Verify teacher is assigned
            if not ClassTeacher.objects.filter(teacher=teacher, school_class=school_class).exists():
                messages.error(request, 'You are not assigned to this class.')
                return redirect('teacher_mark_attendance')

            today = date.today()
            present_count = 0
            absent_count = 0

            # Process attendance for each student
            students = Student.objects.filter(student_class=school_class, status='active')
            for student in students:
                is_present = request.POST.get(f'student_{student.id}') == 'on'
                notes = request.POST.get(f'notes_{student.id}', '')

                attendance, created = AttendanceRecord.objects.update_or_create(
                    student=student,
                    date=today,
                    school_class=school_class,
                    defaults={
                        'present': is_present,
                        'marked_by': request.user,
                        'notes': notes
                    }
                )

                if is_present:
                    present_count += 1
                else:
                    absent_count += 1

            # Create or update attendance session
            session, created = AttendanceSession.objects.update_or_create(
                school_class=school_class,
                date=today,
                defaults={
                    'teacher': teacher,
                    'total_students': len(students),
                    'present_count': present_count,
                    'absent_count': absent_count
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
                    total_records = AttendanceRecord.objects.filter(
                        student=student,
                        school_class=school_class
                    ).count()

                    present_count = AttendanceRecord.objects.filter(
                        student=student,
                        school_class=school_class,
                        present=True
                    ).count()

                    attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0

                    student_stats.append({
                        'student': student,
                        'total_records': total_records,
                        'present_count': present_count,
                        'absent_count': total_records - present_count,
                        'attendance_percentage': round(attendance_percentage, 2)
                    })

                context['student_stats'] = student_stats

            except SchoolClasses.DoesNotExist:
                pass

        return context
