from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.http import JsonResponse
from exams.models import Term, Subject, ClassSubject
from results.models import GradeScale, ResultTemplate
from school_classes.models import SchoolClasses


def is_admin(user):
    """Check if user is admin"""
    return user.is_staff and user.is_superuser


@login_required
def results_settings_dashboard(request):
    """Main dashboard for results settings management"""
    if not is_admin(request.user):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')

    context = {
        'active_terms': Term.objects.filter(is_active=True).count(),
        'all_terms': Term.objects.count(),
        'subjects': Subject.objects.filter(is_active=True).count(),
        'grade_scales': GradeScale.objects.count(),
        'result_templates': ResultTemplate.objects.filter(is_active=True).count(),
        'classes': SchoolClasses.objects.count(),
    }

    return render(request, 'results/admin/settings_dashboard.html', context)


@login_required
def manage_academic_sessions(request):
    """Manage academic sessions/years"""
    if not is_admin(request.user):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')

    terms = Term.objects.all().order_by('-academic_year', 'name')
    academic_years = set(t.academic_year for t in terms)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_session':
            academic_year = request.POST.get('academic_year', '').strip()
            if not academic_year:
                messages.error(request, 'Please enter an academic year.')
                return redirect('manage_academic_sessions')

            # Check if session already exists
            if Term.objects.filter(academic_year=academic_year).exists():
                messages.warning(request, f'Academic session {academic_year} already exists.')
            else:
                # Create three terms for new session
                term_names = [
                    ('first', 'First Term'),
                    ('second', 'Second Term'),
                    ('third', 'Third Term'),
                ]

                for term_code, term_display in term_names:
                    Term.objects.create(
                        name=term_code,
                        display_name=term_display,
                        academic_year=academic_year,
                        is_active=False
                    )

                messages.success(request, f'✓ Academic session {academic_year} created with 3 terms.')

        elif action == 'activate_term':
            term_id = request.POST.get('term_id')
            try:
                term = Term.objects.get(id=term_id)
                
                # Deactivate all other terms in the same academic year
                Term.objects.filter(academic_year=term.academic_year).update(is_active=False)
                
                # Activate selected term
                term.is_active = True
                term.save()
                
                messages.success(request, f'✓ {term} activated. All other terms in {term.academic_year} deactivated.')
            except Term.DoesNotExist:
                messages.error(request, 'Term not found.')

        elif action == 'deactivate_all_current':
            active_count = Term.objects.filter(is_active=True).update(is_active=False)
            messages.success(request, f'✓ Deactivated {active_count} active term(s).')

    context = {
        'terms': terms,
        'academic_years': sorted(academic_years, reverse=True),
        'active_terms': Term.objects.filter(is_active=True),
    }

    return render(request, 'results/admin/manage_academic_sessions.html', context)


@login_required
def bulk_manage_subjects(request):
    """Bulk manage subjects"""
    if not is_admin(request.user):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')

    subjects = Subject.objects.all().order_by('-is_active', 'name')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_subject':
            name = request.POST.get('name', '').strip()
            code = request.POST.get('code', '').strip()
            
            if not name:
                messages.error(request, 'Subject name is required.')
                return redirect('bulk_manage_subjects')

            if Subject.objects.filter(name=name).exists():
                messages.error(request, f'Subject "{name}" already exists.')
            else:
                Subject.objects.create(
                    name=name,
                    code=code if code else None,
                    is_active=True
                )
                messages.success(request, f'✓ Subject "{name}" added successfully.')

        elif action == 'bulk_add_subjects':
            subjects_text = request.POST.get('subjects_text', '').strip()
            if not subjects_text:
                messages.error(request, 'Please enter at least one subject.')
                return redirect('bulk_manage_subjects')

            added = 0
            skipped = 0
            for line in subjects_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split('|')
                name = parts[0].strip()
                code = parts[1].strip() if len(parts) > 1 else ''

                if Subject.objects.filter(name=name).exists():
                    skipped += 1
                else:
                    Subject.objects.create(
                        name=name,
                        code=code if code else None,
                        is_active=True
                    )
                    added += 1

            messages.success(request, f'✓ Added {added} subject(s), skipped {skipped} existing.')

        elif action == 'toggle_subject':
            subject_id = request.POST.get('subject_id')
            try:
                subject = Subject.objects.get(id=subject_id)
                subject.is_active = not subject.is_active
                subject.save()
                status = 'activated' if subject.is_active else 'deactivated'
                messages.success(request, f'✓ Subject "{subject.name}" {status}.')
            except Subject.DoesNotExist:
                messages.error(request, 'Subject not found.')

    context = {
        'subjects': subjects,
        'active_subjects': Subject.objects.filter(is_active=True).count(),
    }

    return render(request, 'results/admin/bulk_manage_subjects.html', context)


@login_required
def bulk_manage_grade_scales(request):
    """Bulk manage grade scales"""
    if not is_admin(request.user):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')

    grade_scales = GradeScale.objects.all().order_by('name', '-min_score')
    unique_scales = set(gs.name for gs in grade_scales)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_grade':
            scale_name = request.POST.get('scale_name', '').strip()
            min_score = request.POST.get('min_score', '')
            max_score = request.POST.get('max_score', '')
            grade = request.POST.get('grade', '').strip()
            remark = request.POST.get('remark', '').strip()
            grade_point = request.POST.get('grade_point', '')

            if not all([scale_name, min_score, max_score, grade, remark]):
                messages.error(request, 'All fields are required.')
                return redirect('bulk_manage_grade_scales')

            try:
                if GradeScale.objects.filter(name=scale_name, grade=grade).exists():
                    messages.error(request, f'Grade "{grade}" already exists in scale "{scale_name}".')
                else:
                    GradeScale.objects.create(
                        name=scale_name,
                        min_score=min_score,
                        max_score=max_score,
                        grade=grade,
                        remark=remark,
                        grade_point=grade_point if grade_point else 0,
                    )
                    messages.success(request, f'✓ Grade "{grade}" added to scale "{scale_name}".')
            except ValueError:
                messages.error(request, 'Please enter valid numeric values.')

        elif action == 'delete_grade':
            grade_id = request.POST.get('grade_id')
            try:
                grade_obj = GradeScale.objects.get(id=grade_id)
                grade_name = str(grade_obj)
                grade_obj.delete()
                messages.success(request, f'✓ Grade {grade_name} deleted.')
            except GradeScale.DoesNotExist:
                messages.error(request, 'Grade not found.')

    context = {
        'grade_scales': grade_scales,
        'unique_scales': sorted(unique_scales),
    }

    return render(request, 'results/admin/bulk_manage_grade_scales.html', context)


@login_required
def bulk_create_result_templates(request):
    """Bulk create result templates for classes"""
    if not is_admin(request.user):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')

    templates = ResultTemplate.objects.all().order_by('-is_active', 'school_class', 'term')
    classes = SchoolClasses.objects.all()
    active_terms = Term.objects.filter(is_active=True)
    grade_scales = GradeScale.objects.values('name').distinct().order_by('name')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_template':
            class_ids = request.POST.getlist('classes')
            term_id = request.POST.get('term')
            scale_name = request.POST.get('scale_name')
            test_max = request.POST.get('test_max_score', 40)
            exam_max = request.POST.get('exam_max_score', 60)

            if not all([class_ids, term_id, scale_name]):
                messages.error(request, 'Please select classes, term, and grade scale.')
                return redirect('bulk_create_result_templates')

            try:
                term = Term.objects.get(id=term_id)
                grade_scale = GradeScale.objects.filter(name=scale_name).first()

                if not grade_scale:
                    messages.error(request, 'Selected grade scale not found.')
                    return redirect('bulk_create_result_templates')

                created = 0
                skipped = 0

                for class_id in class_ids:
                    school_class = SchoolClasses.objects.get(id=class_id)
                    
                    if ResultTemplate.objects.filter(school_class=school_class, term=term).exists():
                        skipped += 1
                        continue

                    ResultTemplate.objects.create(
                        name=f"{school_class} - {term}",
                        school_class=school_class,
                        term=term,
                        grade_scale=grade_scale,
                        test_max_score=test_max,
                        exam_max_score=exam_max,
                        is_active=False
                    )
                    created += 1

                messages.success(request, f'✓ Created {created} template(s), skipped {skipped} existing.')

            except Exception as e:
                messages.error(request, f'Error creating templates: {str(e)}')

        elif action == 'activate_template':
            template_id = request.POST.get('template_id')
            try:
                template = ResultTemplate.objects.get(id=template_id)
                template.is_active = True
                template.save()
                messages.success(request, f'✓ Template "{template.name}" activated.')
            except ResultTemplate.DoesNotExist:
                messages.error(request, 'Template not found.')

        elif action == 'deactivate_template':
            template_id = request.POST.get('template_id')
            try:
                template = ResultTemplate.objects.get(id=template_id)
                template.is_active = False
                template.save()
                messages.success(request, f'✓ Template "{template.name}" deactivated.')
            except ResultTemplate.DoesNotExist:
                messages.error(request, 'Template not found.')

    context = {
        'templates': templates,
        'classes': classes,
        'active_terms': active_terms,
        'grade_scales': grade_scales,
        'active_templates': ResultTemplate.objects.filter(is_active=True).count(),
    }

    return render(request, 'results/admin/bulk_create_result_templates.html', context)


@login_required
def bulk_assign_class_subjects(request):
    """Bulk assign subjects to classes"""
    if not is_admin(request.user):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')

    classes = SchoolClasses.objects.all()
    subjects = Subject.objects.filter(is_active=True)
    assignments = ClassSubject.objects.select_related('school_class', 'subject').all()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'bulk_assign':
            class_id = request.POST.get('class')
            subject_ids = request.POST.getlist('subjects')

            if not class_id or not subject_ids:
                messages.error(request, 'Please select a class and at least one subject.')
                return redirect('bulk_assign_class_subjects')

            try:
                school_class = SchoolClasses.objects.get(id=class_id)
                created = 0
                skipped = 0

                for subject_id in subject_ids:
                    subject = Subject.objects.get(id=subject_id)
                    
                    if ClassSubject.objects.filter(school_class=school_class, subject=subject).exists():
                        skipped += 1
                        continue

                    ClassSubject.objects.create(
                        school_class=school_class,
                        subject=subject,
                        is_compulsory=True,
                        order=ClassSubject.objects.filter(school_class=school_class).count() + 1
                    )
                    created += 1

                messages.success(request, f'✓ Assigned {created} subject(s) to {school_class}, skipped {skipped} existing.')

            except Exception as e:
                messages.error(request, f'Error assigning subjects: {str(e)}')

        elif action == 'remove_assignment':
            assignment_id = request.POST.get('assignment_id')
            try:
                assignment = ClassSubject.objects.get(id=assignment_id)
                class_name = assignment.school_class.class_name
                subject_name = assignment.subject.name
                assignment.delete()
                messages.success(request, f'✓ Removed "{subject_name}" from "{class_name}".')
            except ClassSubject.DoesNotExist:
                messages.error(request, 'Assignment not found.')

    context = {
        'classes': classes,
        'subjects': subjects,
        'assignments': assignments,
        'total_assignments': assignments.count(),
    }

    return render(request, 'results/admin/bulk_assign_class_subjects.html', context)
