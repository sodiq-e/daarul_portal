import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, ListView, FormView

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import AttendanceSettingsForm, StudentAttendanceSettingsForm
from .models import AttendanceSettings, StudentAttendanceSettings, StaffAttendance, calculate_distance_meters


class StaffAttendanceDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'staff_attendance/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not hasattr(self.request.user, 'teacher_profile'):
            context['permission_denied'] = True
            return context

        teacher = self.request.user.teacher_profile
        today = timezone.localdate()
        context['attendance_settings'] = AttendanceSettings.get_current()
        context['current_attendance'] = StaffAttendance.objects.filter(
            teacher=teacher,
            date=today
        ).first()
        context['monthly_summary'] = StaffAttendance.objects.filter(
            teacher=teacher,
            date__month=today.month,
            date__year=today.year
        ).order_by('-date')
        return context


class AttendanceHistoryView(LoginRequiredMixin, ListView):
    template_name = 'staff_attendance/history.html'
    context_object_name = 'attendances'
    paginate_by = 25

    def get_queryset(self):
        if not hasattr(self.request.user, 'teacher_profile'):
            return StaffAttendance.objects.none()
        teacher = self.request.user.teacher_profile
        return StaffAttendance.objects.filter(teacher=teacher).order_by('-date')


class MonthlyReportView(LoginRequiredMixin, TemplateView):
    template_name = 'staff_attendance/monthly_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not hasattr(self.request.user, 'teacher_profile'):
            context['permission_denied'] = True
            return context

        teacher = self.request.user.teacher_profile
        today = timezone.localdate()
        records = StaffAttendance.objects.filter(
            teacher=teacher,
            date__month=today.month,
            date__year=today.year
        )
        context['attendance_settings'] = AttendanceSettings.get_current()
        context['records'] = records
        context['present_count'] = records.filter(clock_in_status=StaffAttendance.STATUS_PRESENT).count()
        context['late_count'] = records.filter(clock_in_status=StaffAttendance.STATUS_LATE).count()
        context['absent_count'] = records.filter(clock_in_status=StaffAttendance.STATUS_ABSENT).count()

        total_work_seconds = sum(
            int((record.clock_out - record.clock_in).total_seconds())
            for record in records
            if record.clock_in and record.clock_out and record.clock_out >= record.clock_in
        )
        total_work_hours = total_work_seconds / 3600 if total_work_seconds else 0
        average_clock_in_seconds = 0
        clock_in_records = [record for record in records if record.clock_in]
        if clock_in_records:
            average_clock_in_seconds = sum(
                record.clock_in.hour * 3600 + record.clock_in.minute * 60 + record.clock_in.second
                for record in clock_in_records
            ) // len(clock_in_records)

        average_clock_in_time = timezone.datetime(2000, 1, 1, tzinfo=timezone.get_default_timezone()) + timezone.timedelta(seconds=average_clock_in_seconds) if clock_in_records else None
        context['hours_worked'] = total_work_hours
        context['hours_worked_formatted'] = f"{int(total_work_hours)}h {int((total_work_hours * 60) % 60)}m"
        if average_clock_in_time:
            clock_in_display = average_clock_in_time.strftime('%I:%M %p')
            context['average_clock_in'] = clock_in_display.lstrip('0') if clock_in_display.startswith('0') else clock_in_display
        else:
            context['average_clock_in'] = None
        return context


class AttendanceSettingsView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'staff_attendance/settings_form.html'
    form_class = AttendanceSettingsForm
    success_url = reverse_lazy('staff_attendance:settings')

    def test_func(self):
        return self.request.user.is_staff

    def get_initial(self):
        active_settings = AttendanceSettings.get_current()
        if active_settings.pk:
            return {
                'school_latitude': active_settings.school_latitude,
                'school_longitude': active_settings.school_longitude,
                'allowed_radius_meters': active_settings.allowed_radius_meters,
                'normal_clock_in_time': active_settings.normal_clock_in_time,
                'late_after_time': active_settings.late_after_time,
                'earliest_clock_out_time': active_settings.earliest_clock_out_time,
                'enable_gps_verification': active_settings.enable_gps_verification,
                'enable_clock_out': active_settings.enable_clock_out,
                'enable_offline_sync': active_settings.enable_offline_sync,
                'active': active_settings.active,
            }
        return super().get_initial()

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Staff attendance settings have been saved.')
        return super().form_valid(form)


class StudentAttendanceSettingsView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'staff_attendance/student_settings_form.html'
    form_class = StudentAttendanceSettingsForm
    success_url = reverse_lazy('staff_attendance:student_settings')

    def test_func(self):
        return self.request.user.is_staff

    def get_initial(self):
        active = StudentAttendanceSettings.get_current()
        if getattr(active, 'pk', None):
            return {
                'enable_student_attendance': active.enable_student_attendance,
                'require_daily_checkin': active.require_daily_checkin,
                'allow_parent_reason_submission': active.allow_parent_reason_submission,
                'absence_threshold_warning': active.absence_threshold_warning,
                'active': active.active,
            }
        return super().get_initial()

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Student attendance settings have been saved.')
        return super().form_valid(form)


class StaffAttendanceBaseAPI(LoginRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get_teacher(self):
        if not hasattr(self.request.user, 'teacher_profile'):
            return None
        return self.request.user.teacher_profile

    def validate_gps(self, settings, latitude, longitude):
        if not settings.enable_gps_verification:
            return None
        if settings.school_latitude is None or settings.school_longitude is None:
            return 'Attendance configuration does not include school coordinates.'
        if latitude is None or longitude is None:
            return 'Location is required when GPS verification is enabled.'
        distance = calculate_distance_meters(
            latitude,
            longitude,
            settings.school_latitude,
            settings.school_longitude,
        )
        if distance is None:
            return 'Unable to parse GPS coordinates.'
        if distance > Decimal(settings.allowed_radius_meters):
            return f'You are too far from school to record attendance ({int(distance)}m outside allowed radius).'
        return None

    def get_decimal_coordinate(self, value):
        try:
            return Decimal(str(value))
        except (TypeError, ValueError):
            return None

    def validate_school_coordinates(self, settings):
        if settings.school_latitude is None or settings.school_longitude is None:
            return 'Attendance location not configured. Contact administrator.'
        return None

    def parse_uuid(self, value):
        if not value:
            return None
        try:
            return UUID(str(value))
        except Exception:
            return None

    def parse_client_timestamp(self, value):
        if not value:
            return None
        try:
            ts = datetime.fromisoformat(value)
            if ts.tzinfo is None:
                ts = timezone.make_aware(ts)
            return ts
        except Exception:
            return None

    def mark_suspicious(self, server_time, client_time, offline=False):
        if not client_time:
            return False
        delta_seconds = abs((server_time - client_time).total_seconds())
        if delta_seconds >= 6 * 3600:
            return True
        if delta_seconds >= 30 * 60 and not offline:
            return True
        return False


class StaffAttendanceClockInAPI(StaffAttendanceBaseAPI):
    def post(self, request, *args, **kwargs):
        teacher = self.get_teacher()
        if teacher is None:
            return Response({'detail': 'Only teachers may use staff attendance.'}, status=status.HTTP_403_FORBIDDEN)

        attendance_settings = AttendanceSettings.get_current()
        today = timezone.localdate()
        if StaffAttendance.objects.filter(teacher=teacher, date=today).exists():
            return Response({'detail': 'You have already clocked in today.'}, status=status.HTTP_400_BAD_REQUEST)

        location_error = self.validate_school_coordinates(attendance_settings)
        if location_error:
            return Response({'detail': location_error}, status=status.HTTP_400_BAD_REQUEST)

        latitude = self.get_decimal_coordinate(request.data.get('latitude'))
        longitude = self.get_decimal_coordinate(request.data.get('longitude'))
        offline_record = bool(request.data.get('offline_record', False))
        device_info = request.data.get('device_info', '').strip()
        offline_sync_id = self.parse_uuid(request.data.get('offline_sync_id'))
        client_timestamp = self.parse_client_timestamp(request.data.get('timestamp'))

        if offline_record and not offline_sync_id:
            offline_sync_id = uuid.uuid4()

        if offline_sync_id and StaffAttendance.objects.filter(offline_sync_id=offline_sync_id).exists():
            return Response({'detail': 'This offline attendance record has already been synced.'}, status=status.HTTP_400_BAD_REQUEST)

        gps_error = self.validate_gps(attendance_settings, latitude, longitude)
        if gps_error:
            return Response({'detail': gps_error}, status=status.HTTP_400_BAD_REQUEST)

        server_time = timezone.localtime()
        client_time_for_suspicion = client_timestamp or server_time
        is_suspicious = self.mark_suspicious(server_time, client_time_for_suspicion, offline=offline_record)
        status_value = StaffAttendance.STATUS_LATE if server_time.time() > attendance_settings.late_after_time else StaffAttendance.STATUS_PRESENT
        record = StaffAttendance.objects.create(
            teacher=teacher,
            date=today,
            clock_in=server_time,
            clock_in_latitude=latitude,
            clock_in_longitude=longitude,
            clock_in_status=status_value,
            synced=not offline_record,
            sync_time=server_time if not offline_record else None,
            offline_sync_id=offline_sync_id,
            device_info=device_info,
            offline_record=offline_record,
            is_suspicious=is_suspicious,
        )

        return Response({
            'message': 'Clock in recorded.',
            'status': status_value,
            'clock_in': record.clock_in,
            'synced': record.synced,
            'offline_record': record.offline_record,
        }, status=status.HTTP_201_CREATED)


class StaffAttendanceClockOutAPI(StaffAttendanceBaseAPI):
    def post(self, request, *args, **kwargs):
        teacher = self.get_teacher()
        if teacher is None:
            return Response({'detail': 'Only teachers may use staff attendance.'}, status=status.HTTP_403_FORBIDDEN)

        attendance_settings = AttendanceSettings.get_current()
        today = timezone.localdate()
        record = StaffAttendance.objects.filter(teacher=teacher, date=today).first()
        if not record or not record.clock_in:
            return Response({'detail': 'Clock in must exist before you can clock out.'}, status=status.HTTP_400_BAD_REQUEST)
        if not attendance_settings.enable_clock_out:
            return Response({'detail': 'Clock out is disabled by current settings.'}, status=status.HTTP_403_FORBIDDEN)
        if record.clock_out:
            return Response({'detail': 'You have already clocked out today.'}, status=status.HTTP_400_BAD_REQUEST)

        location_error = self.validate_school_coordinates(attendance_settings)
        if location_error:
            return Response({'detail': location_error}, status=status.HTTP_400_BAD_REQUEST)

        latitude = self.get_decimal_coordinate(request.data.get('latitude'))
        longitude = self.get_decimal_coordinate(request.data.get('longitude'))
        offline_record = bool(request.data.get('offline_record', False))
        device_info = request.data.get('device_info', '').strip()
        offline_sync_id = self.parse_uuid(request.data.get('offline_sync_id'))
        client_timestamp = self.parse_client_timestamp(request.data.get('timestamp'))

        if offline_record and not offline_sync_id:
            offline_sync_id = uuid.uuid4()

        if offline_sync_id and StaffAttendance.objects.filter(offline_sync_id=offline_sync_id).exists():
            return Response({'detail': 'This offline attendance record has already been synced.'}, status=status.HTTP_400_BAD_REQUEST)

        gps_error = self.validate_gps(attendance_settings, latitude, longitude)
        if gps_error:
            return Response({'detail': gps_error}, status=status.HTTP_400_BAD_REQUEST)

        server_time = timezone.localtime()
        if server_time.time() < attendance_settings.earliest_clock_out_time:
            return Response({
                'detail': 'You cannot clock out before the configured earliest clock-out time.'
            }, status=status.HTTP_400_BAD_REQUEST)

        client_time_for_suspicion = client_timestamp or server_time
        is_suspicious = self.mark_suspicious(server_time, client_time_for_suspicion, offline=offline_record)

        record.clock_out = server_time
        record.clock_out_latitude = latitude
        record.clock_out_longitude = longitude
        record.device_info = device_info or record.device_info
        record.synced = not offline_record
        record.offline_record = offline_record
        record.sync_time = server_time if not offline_record else None
        record.offline_sync_id = offline_sync_id or record.offline_sync_id
        record.is_suspicious = record.is_suspicious or is_suspicious
        record.save()

        return Response({
            'message': 'Clock out recorded.',
            'clock_out': record.clock_out,
            'synced': record.synced,
            'offline_record': record.offline_record,
        }, status=status.HTTP_200_OK)


class StaffAttendanceSyncAPI(StaffAttendanceBaseAPI):
    def post(self, request, *args, **kwargs):
        attendance_settings = AttendanceSettings.get_current()
        if not attendance_settings.enable_offline_sync:
            return Response({'detail': 'Offline sync is disabled.'}, status=status.HTTP_403_FORBIDDEN)

        location_error = self.validate_school_coordinates(attendance_settings)
        if location_error:
            return Response({'detail': location_error}, status=status.HTTP_400_BAD_REQUEST)

        teacher = self.get_teacher()
        if teacher is None:
            return Response({'detail': 'Only teachers may sync attendance.'}, status=status.HTTP_403_FORBIDDEN)

        records = request.data.get('records', [])
        if not isinstance(records, list):
            return Response({'detail': 'Records must be an array.'}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        for item in records:
            attendance_type = item.get('attendance_type')
            timestamp_value = item.get('timestamp')
            latitude = self.get_decimal_coordinate(item.get('latitude'))
            longitude = self.get_decimal_coordinate(item.get('longitude'))
            device_info = item.get('device_info', '').strip()
            offline_sync_id = self.parse_uuid(item.get('offline_sync_id'))
            client_timestamp = self.parse_client_timestamp(timestamp_value)

            if attendance_type not in ['clock_in', 'clock_out']:
                results.append({'item': item, 'error': 'Invalid attendance type.'})
                continue

            if offline_sync_id and StaffAttendance.objects.filter(offline_sync_id=offline_sync_id).exists():
                results.append({'item': item, 'error': 'This offline attendance record has already been synced.'})
                continue

            try:
                timestamp = timezone.make_aware(datetime.fromisoformat(timestamp_value))
            except Exception:
                results.append({'item': item, 'error': 'Invalid timestamp format.'})
                continue

            if attendance_settings.enable_gps_verification:
                gps_error = self.validate_gps(attendance_settings, latitude, longitude)
                if gps_error:
                    results.append({'item': item, 'error': gps_error})
                    continue

            record_date = timestamp.date()
            record, created = StaffAttendance.objects.get_or_create(
                teacher=teacher,
                date=record_date,
                defaults={
                    'clock_in': timestamp if attendance_type == 'clock_in' else None,
                    'clock_out': timestamp if attendance_type == 'clock_out' else None,
                    'clock_in_latitude': latitude if attendance_type == 'clock_in' else None,
                    'clock_in_longitude': longitude if attendance_type == 'clock_in' else None,
                    'clock_out_latitude': latitude if attendance_type == 'clock_out' else None,
                    'clock_out_longitude': longitude if attendance_type == 'clock_out' else None,
                    'clock_in_status': StaffAttendance.STATUS_LATE if attendance_type == 'clock_in' and timestamp.time() > attendance_settings.late_after_time else StaffAttendance.STATUS_PRESENT,
                    'synced': True,
                    'sync_time': timezone.now(),
                    'offline_sync_id': offline_sync_id,
                    'device_info': device_info,
                    'offline_record': True,
                    'is_suspicious': self.mark_suspicious(timezone.localtime(), client_timestamp or timezone.localtime(), offline=True),
                }
            )

            if not created:
                if attendance_type == 'clock_in':
                    if record.clock_in:
                        results.append({'item': item, 'error': 'Clock-in already recorded for this date.'})
                        continue
                    record.clock_in = timestamp
                    record.clock_in_latitude = latitude
                    record.clock_in_longitude = longitude
                    record.clock_in_status = StaffAttendance.STATUS_LATE if timestamp.time() > attendance_settings.late_after_time else StaffAttendance.STATUS_PRESENT
                else:
                    if not record.clock_in:
                        results.append({'item': item, 'error': 'Clock-out requires an existing clock-in.'})
                        continue
                    if record.clock_out:
                        results.append({'item': item, 'error': 'Clock-out already recorded for this date.'})
                        continue
                    if timestamp.time() < attendance_settings.earliest_clock_out_time:
                        results.append({'item': item, 'error': 'Clock-out time is earlier than allowed.'})
                        continue
                    record.clock_out = timestamp
                    record.clock_out_latitude = latitude
                    record.clock_out_longitude = longitude

            record.device_info = device_info or record.device_info
            record.synced = True
            record.sync_time = timezone.now()
            record.offline_record = True
            record.offline_sync_id = offline_sync_id or record.offline_sync_id
            record.is_suspicious = record.is_suspicious or self.mark_suspicious(timezone.localtime(), client_timestamp or timezone.localtime(), offline=True)
            record.save()
            results.append({'item': item, 'status': 'synced'})

        return Response({'results': results}, status=status.HTTP_200_OK)
