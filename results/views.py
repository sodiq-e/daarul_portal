from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from django.db.models import Avg, Count, Sum, Q
from students.models import Student
from exams.models import Term, ClassSubject
from school_classes.models import SchoolClasses
from .models import (
    StudentResult, TermResult, ResultTemplate,
    GradeScale, Promotion, ReportCardComment
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

    # Get all students in this class
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

    context = {
        'school_class': school_class,
        'term': term,
        'result_template': result_template,
        'student_results': student_results,
        'can_modify': user_is_staff(request.user),
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
    if not user_is_staff(request.user) and student.admission_no != request.user.username:
        messages.error(request, 'You do not have permission to view this report card.')
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
        return redirect('results_home')

    # Get student results
    results = StudentResult.objects.filter(
        student=student,
        term=term,
        result_template=result_template
    ).select_related('class_subject__subject').order_by('class_subject__order')

    # Get term result
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

    return render(request, 'results/student_report_card.html', context)


@login_required
def broadsheet(request, class_id, term_id):
    """Generate printable broadsheet for a class"""
    if not user_is_staff(request.user):
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

    # Get all subjects for this class
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

        # Get results for each subject
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

        # Get term result
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
    if not user_is_staff(request.user):
        messages.error(request, 'You do not have permission to view promotions.')
        return redirect('home')

    promotions = Promotion.objects.select_related(
        'student', 'from_class', 'to_class', 'term'
    ).order_by('-promoted_date')

    return render(request, 'results/promotions_list.html', {'promotions': promotions})


@login_required
def promote_student(request, student_id, exam_id):
    if not user_is_staff(request.user):
        messages.error(request, 'You do not have permission to promote students.')
        return redirect('home')

    student = get_object_or_404(Student, pk=student_id)
    # For backward compatibility, we'll redirect to the new system
    messages.info(request, 'Student promotion has been moved to the new results system.')
    return redirect('results_home')




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
def teacher_results_list(request):
    """Teachers view results for their classes"""
    try:
        teacher = request.user.teacher_profile
    except:
        messages.error(request, 'You must be a teacher to access this page.')
        return redirect('home')

    if not teacher_has_permission(teacher, 'view_results'):
        messages.error(request, 'You do not have permission to view results.')
        return redirect('home')

    # Get classes assigned to this teacher
    from school_classes.models import ClassTeacher
    assigned_classes = ClassTeacher.objects.filter(
        teacher=teacher,
        is_active=True
    ).values_list('school_class_id', flat=True).distinct()

    # Get terms
    terms = Term.objects.filter(is_active=True)

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

    context = {
        'school_class': school_class,
        'term': term,
        'result_template': result_template,
        'student_results': student_results,
        'can_edit': True,  # Show bulk entry button if teacher is assigned to class
        'can_print': teacher_has_permission(teacher, 'print_results'),
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
            
            # Calculate aggregates
            result.calculate_aggregates()

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
    results_by_student_subject = {}
    for student in students:
        results_by_student_subject[student.id] = {}
        for class_subject in class_subjects:
            result = StudentResult.objects.filter(
                student=student,
                class_subject=class_subject,
                term=term,
                result_template=result_template
            ).first()
            results_by_student_subject[student.id][class_subject.id] = result

    if request.method == 'POST':
        # Process POST data and save results
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

        messages.success(request, f'✓ Results saved successfully for {len(students)} students!')
        return redirect('teacher_class_results', class_id=class_id, term_id=term_id)

    context = {
        'school_class': school_class,
        'term': term,
        'result_template': result_template,
        'students': students,
        'class_subjects': class_subjects,
        'results_by_student_subject': results_by_student_subject,
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

    from .forms import ReportCardCommentForm

    if request.method == 'POST':
        form = ReportCardCommentForm(request.POST, instance=report_comment)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.term_result = term_result
            comment.teacher = teacher
            comment.created_by = request.user
            comment.save()
            messages.success(request, 'Report card comment saved successfully.')
            return redirect('teacher_class_results', class_id=student.student_class.id, term_id=term.id)
    else:
        form = ReportCardCommentForm(instance=report_comment)

    # Get student results for display
    results = StudentResult.objects.filter(
        student=student,
        term=term,
        result_template=result_template
    ).select_related('class_subject__subject').order_by('class_subject__order')

    context = {
        'student': student,
        'term': term,
        'term_result': term_result,
        'results': results,
        'form': form,
        'comment': report_comment
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
