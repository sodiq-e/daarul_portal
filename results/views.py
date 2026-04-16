from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from students.models import Student
from exams.models import Exam, Subject
from .models import Score, Promotion


@login_required
def results_home(request):
    if not request.user.profile.is_approved:
        from django.contrib import messages
        messages.error(request, 'Your account is not approved yet.')
        return redirect('home')

    score_entries = Score.objects.order_by('exam__date', 'student__surname').values(
        'student_id', 'student__admission_no', 'student__surname', 'student__other_names',
        'exam_id', 'exam__name'
    ).distinct()
    result_items = [
        {
            'student_id': entry['student_id'],
            'exam_id': entry['exam_id'],
            'student_name': f"{entry['student__surname']} {entry['student__other_names'] or ''}".strip(),
            'admission_no': entry['student__admission_no'],
            'exam_name': entry['exam__name'],
        }
        for entry in score_entries
    ]
    exams = Exam.objects.filter(score__isnull=False).distinct()
    return render(request, 'results/results_home.html', {'result_items': result_items, 'exams': exams})


@login_required
def report_card(request, student_id, exam_id):
    if not request.user.profile.is_approved:
        from django.contrib import messages
        messages.error(request, 'Your account is not approved yet.')
        return redirect('home')

    student = get_object_or_404(Student, pk=student_id)
    exam = get_object_or_404(Exam, pk=exam_id)
    scores = Score.objects.filter(student=student, exam=exam).select_related('subject')
    total = sum([float(s.score) for s in scores]) if scores else 0
    count = scores.count()
    average = (total / count) if count else 0.0
    students = Student.objects.all()
    totals = []
    for st in students:
        st_total = sum([float(x.score) for x in Score.objects.filter(student=st, exam=exam)])
        totals.append((st, st_total))
    totals_sorted = sorted(totals, key=lambda x: x[1], reverse=True)
    position = next((i+1 for i,(st,tot) in enumerate(totals_sorted) if st.pk==student.pk), None)
    def grade_from_avg(avg):
        if avg >= 70:
            return 'A'
        if avg >= 60:
            return 'B'
        if avg >= 50:
            return 'C'
        if avg >= 45:
            return 'D'
        if avg >= 40:
            return 'E'
        return 'F'
    overall_grade = grade_from_avg(average)
    context = {
        'student': student,
        'exam': exam,
        'scores': scores,
        'total': total,
        'average': round(average, 2),
        'position': position,
        'overall_grade': overall_grade,
    }
    return render(request, 'results_report.html', context)


@login_required
def promotions_list(request):
    if not request.user.is_staff:
        return redirect('home')
    promotions = Promotion.objects.select_related('student', 'from_class', 'to_class', 'exam').order_by('-promoted_date')
    return render(request, 'results/promotions_list.html', {'promotions': promotions})


@login_required
def promote_student(request, student_id, exam_id):
    if not request.user.is_staff:
        return redirect('home')
    student = get_object_or_404(Student, pk=student_id)
    exam = get_object_or_404(Exam, pk=exam_id)
    if request.method == 'POST':
        to_class_id = request.POST.get('to_class')
        remarks = request.POST.get('remarks', '')
        from school_classes.models import SchoolClasses
        to_class = get_object_or_404(SchoolClasses, pk=to_class_id)
        Promotion.objects.create(
            student=student,
            from_class=student.student_class,
            to_class=to_class,
            exam=exam,
            remarks=remarks
        )
        student.student_class = to_class
        student.save()
        return redirect('promotions_list')
    classes = SchoolClasses.objects.all()
    return render(request, 'results/promote_student.html', {
        'student': student,
        'exam': exam,
        'classes': classes
    })


@login_required
def broadsheet(request, exam_id):
    if not request.user.is_staff:
        return redirect('home')
    exam = get_object_or_404(Exam, pk=exam_id)
    students = Student.objects.filter(status='active').order_by('surname', 'other_names')
    subjects = Subject.objects.filter(exam__id=exam_id).distinct()
    scores_data = {}
    totals = {}
    averages = {}
    for student in students:
        scores_data[student.id] = {}
        total = 0
        count = 0
        for subject in subjects:
            score = Score.objects.filter(student=student, exam=exam, subject=subject).first()
            scores_data[student.id][subject.id] = score.score if score else '-'
            if score:
                total += float(score.score)
                count += 1
        totals[student.id] = total
        averages[student.id] = total / count if count else 0
    # Sort students by total descending for positions
    sorted_students = sorted(students, key=lambda s: totals.get(s.id, 0), reverse=True)
    positions = {}
    for i, student in enumerate(sorted_students, 1):
        positions[student.id] = i
    return render(request, 'results/broadsheet.html', {
        'exam': exam,
        'students': students,
        'subjects': subjects,
        'scores_data': scores_data,
        'totals': totals,
        'averages': averages,
        'positions': positions
    })
