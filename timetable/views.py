from copy import copy

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from exams.models import ClassSubject, Term
from school_classes.models import ClassTeacher, SchoolClasses, Teacher
from settingsapp.tenant_utils import get_request_tenant, user_is_tenant_admin, user_is_tenant_staff
from students.models import Student

from .forms import TimetableSlotForm, TimetableTemplateForm
from .models import TimetableDay, TimetableEntry, TimetableSlot, TimetableTemplate


DAY_DEFAULTS = [
    ('monday', False), ('tuesday', False), ('wednesday', False),
    ('thursday', False), ('friday', True), ('saturday', False),
]


def _approved(user):
    if user.is_superuser:
        return True
    try:
        return user.profile.is_approved
    except AttributeError:
        return False


def _admin(request):
    return request.user.is_superuser or user_is_tenant_admin(
        request.user, tenant=get_request_tenant(request)
    )


def _staff(request):
    return user_is_tenant_staff(request.user, tenant=get_request_tenant(request))


def _teacher_for_user(user):
    if user is None or not getattr(user, 'is_authenticated', False):
        return None
    try:
        return user.teacher_profile
    except Teacher.DoesNotExist:
        pass
    return Teacher.objects.filter(user=user).first()


def _can_edit(request, timetable):
    if _admin(request):
        return True
    if not _staff(request):
        return False
    teacher = _teacher_for_user(request.user)
    if teacher is None:
        return False
    return ClassTeacher.objects.filter(
        teacher=teacher,
        school_class=timetable.school_class,
        is_active=True,
    ).exists()


def _visible_timetables(request):
    queryset = TimetableTemplate.objects.select_related('term', 'school_class')
    if _admin(request) or _staff(request):
        return queryset
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        return queryset.filter(is_published=True)
    if student.student_class_id:
        return queryset.filter(school_class_id=student.student_class_id, is_published=True)
    return queryset.none()


def _grid_context(timetable):
    days = list(timetable.days.all())
    slots = list(timetable.slots.all())
    entry_map = {
        (entry.slot_id, entry.day_id): entry
        for entry in timetable.entries.select_related('class_subject__subject', 'teacher__user')
    }
    rows = [
        {
            'slot': slot,
            'cells': [
                {'day': day, 'entry': entry_map.get((slot.id, day.id))}
                for day in days
            ],
        }
        for slot in slots
    ]
    return {'days': days, 'slots': slots, 'grid_rows': rows}


@login_required
def timetable_list(request):
    if not _approved(request.user):
        messages.error(request, 'Your account is not approved yet.')
        return redirect('home')

    selected_class = request.GET.get('class')
    timetables = _visible_timetables(request)
    if selected_class:
        timetables = timetables.filter(school_class_id=selected_class)
    classes = SchoolClasses.objects.filter(
        id__in=_visible_timetables(request).values('school_class_id')
    ).order_by('class_name')
    context = {
        'timetables': timetables.order_by('school_class__class_name', '-term__academic_year', 'term__name'),
        'classes': classes,
        'selected_class': selected_class,
        'can_manage': _admin(request),
    }
    return render(request, 'timetable/timetable_list.html', context)


@login_required
def timetable_detail(request, pk):
    if not _approved(request.user):
        return redirect('home')
    timetable = get_object_or_404(
        _visible_timetables(request).prefetch_related('days', 'slots'), pk=pk
    )
    can_edit = _can_edit(request, timetable)
    if not timetable.is_published and not can_edit:
        messages.error(request, 'This timetable has not been published.')
        return redirect('timetable:list')
    context = {
        'timetable': timetable,
        'can_edit': can_edit,
        'can_manage': _admin(request),
        'class_subjects': ClassSubject.objects.filter(
            school_class=timetable.school_class
        ).select_related('subject').order_by('order', 'subject__name'),
        'teachers': Teacher.objects.filter(
            class_assignments__school_class=timetable.school_class,
            class_assignments__is_active=True,
        ).select_related('user').distinct(),
        'copy_terms': Term.objects.order_by('-academic_year', 'name'),
        'copy_classes': SchoolClasses.objects.order_by('class_name'),
        'day_choices': TimetableDay.DAY_CHOICES,
    }
    context.update(_grid_context(timetable))
    return render(request, 'timetable/timetable_detail.html', context)


@login_required
def timetable_create(request):
    if not _admin(request):
        messages.error(request, 'Only school administrators can create timetables.')
        return redirect('timetable:list')
    form = TimetableTemplateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        timetable = form.save(commit=False)
        timetable.tenant = get_request_tenant(request)
        timetable.save()
        for order, (day, is_short_day) in enumerate(DAY_DEFAULTS):
            TimetableDay.objects.create(
                tenant=timetable.tenant,
                timetable=timetable,
                day=day,
                order=order,
                is_short_day=is_short_day,
            )
        messages.success(request, 'Timetable template created. Add time rows and fill the subjects.')
        return redirect('timetable:detail', pk=timetable.pk)
    return render(request, 'timetable/timetable_form.html', {'form': form, 'title': 'Create timetable template'})


@login_required
def timetable_copy(request, pk):
    source = get_object_or_404(TimetableTemplate, pk=pk)
    if not _admin(request):
        messages.error(request, 'Only school administrators can copy timetables.')
        return redirect('timetable:detail', pk=pk)
    if request.method != 'POST':
        return redirect('timetable:detail', pk=pk)
    term = get_object_or_404(Term, pk=request.POST.get('term'))
    school_class = get_object_or_404(SchoolClasses, pk=request.POST.get('school_class'))
    name = request.POST.get('name', '').strip() or f'{school_class} - {term}'
    tenant = get_request_tenant(request)
    with transaction.atomic():
        target, created = TimetableTemplate.objects.get_or_create(
            tenant=tenant,
            term=term,
            school_class=school_class,
            defaults={'name': name, 'copied_from': source, 'is_published': False},
        )
        if not created:
            messages.error(request, 'A timetable already exists for that class and term.')
            return redirect('timetable:detail', pk=source.pk)
        day_map = {}
        for day in source.days.all():
            day_map[day.id] = TimetableDay.objects.create(
                tenant=tenant, timetable=target, day=day.day,
                order=day.order, is_short_day=day.is_short_day,
            )
        slot_map = {}
        for slot in source.slots.all():
            slot_map[slot.id] = TimetableSlot.objects.create(
                tenant=tenant, timetable=target, label=slot.label,
                slot_type=slot.slot_type, start_time=slot.start_time,
                end_time=slot.end_time, order=slot.order,
            )
        for entry in source.entries.all():
            TimetableEntry.objects.create(
                tenant=tenant, timetable=target,
                day=day_map[entry.day_id], slot=slot_map[entry.slot_id],
                class_subject=ClassSubject.objects.filter(
                    school_class=school_class, subject_id=entry.class_subject.subject_id
                ).first() if entry.class_subject_id else None,
                teacher=None, note=entry.note,
            )
    messages.success(request, 'Timetable copied. Review the subjects before publishing.')
    return redirect('timetable:detail', pk=target.pk)


@login_required
def timetable_add_slot(request, pk):
    timetable = get_object_or_404(TimetableTemplate, pk=pk)
    if not _admin(request):
        return redirect('timetable:detail', pk=pk)
    form = TimetableSlotForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        slot = form.save(commit=False)
        slot.tenant = get_request_tenant(request)
        slot.timetable = timetable
        slot.save()
        messages.success(request, 'Time row added.')
        return redirect('timetable:detail', pk=pk)
    context = {'form': form, 'timetable': timetable, 'title': 'Add timetable row'}
    return render(request, 'timetable/slot_form.html', context)


@login_required
def timetable_delete_slot(request, pk, slot_id):
    timetable = get_object_or_404(TimetableTemplate, pk=pk)
    if request.method == 'POST' and _admin(request):
        TimetableSlot.objects.filter(timetable=timetable, pk=slot_id).delete()
        messages.success(request, 'Time row deleted.')
    return redirect('timetable:detail', pk=pk)


@login_required
def timetable_remove_day(request, pk, day_id):
    timetable = get_object_or_404(TimetableTemplate, pk=pk)
    if request.method == 'POST' and _admin(request):
        TimetableDay.objects.filter(timetable=timetable, pk=day_id).delete()
        messages.success(request, 'Day column removed.')
    return redirect('timetable:detail', pk=pk)


@login_required
def timetable_add_day(request, pk):
    timetable = get_object_or_404(TimetableTemplate, pk=pk)
    if not _admin(request):
        return redirect('timetable:detail', pk=pk)
    day = request.POST.get('day')
    if request.method == 'POST' and day in dict(TimetableDay.DAY_CHOICES):
        if not TimetableDay.objects.filter(timetable=timetable, day=day).exists():
            next_order = timetable.days.count()
            TimetableDay.objects.create(
                tenant=get_request_tenant(request), timetable=timetable,
                day=day, order=next_order, is_short_day=day == 'friday',
            )
            messages.success(request, 'Day column added.')
    return redirect('timetable:detail', pk=pk)


@login_required
def timetable_fill(request, pk):
    timetable = get_object_or_404(TimetableTemplate, pk=pk)
    if request.method != 'POST' or not _can_edit(request, timetable):
        return redirect('timetable:detail', pk=pk)
    tenant = get_request_tenant(request)
    allowed_subjects = {
        str(item.id): item
        for item in ClassSubject.objects.filter(school_class=timetable.school_class)
    }
    subject_name_map = {
        item.subject.name.strip().lower(): item
        for item in allowed_subjects.values()
        if item.subject and item.subject.name
    }
    teacher = getattr(request.user, 'teacher_profile', None)
    for day in timetable.days.all():
        for slot in timetable.slots.all():
            raw_value = request.POST.get(f'entry_{day.id}_{slot.id}', '').strip()
            note = request.POST.get(f'note_{day.id}_{slot.id}', '').strip()
            subject = None
            if slot.slot_type == 'period' and raw_value:
                subject = allowed_subjects.get(raw_value)
                if subject is None:
                    subject = subject_name_map.get(raw_value.lower())
            assigned_teacher = teacher if teacher and slot.slot_type == 'period' else None
            TimetableEntry.objects.update_or_create(
                tenant=tenant, timetable=timetable, day=day, slot=slot,
                defaults={
                    'class_subject': subject,
                    'teacher': assigned_teacher,
                    'note': note,
                },
            )
    messages.success(request, 'Timetable subjects saved.')
    return redirect('timetable:detail', pk=pk)


@login_required
def timetable_publish(request, pk):
    timetable = get_object_or_404(TimetableTemplate, pk=pk)
    if request.method == 'POST' and _admin(request):
        timetable.is_published = request.POST.get('is_published') == 'on'
        timetable.save(update_fields=['is_published', 'updated_at'])
        messages.success(request, 'Timetable publication status updated.')
    return redirect('timetable:detail', pk=pk)
