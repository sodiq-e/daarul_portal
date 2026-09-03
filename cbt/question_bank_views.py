from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponseForbidden
from .models import QuestionBank, CBTQuestion, CBTChoice
from .forms import QuestionBankForm, CBTQuestionForm, CBTChoiceFormSet
from exams.models import Subject, Term
from school_classes.models import SchoolClasses
from settingsapp.tenant_utils import get_request_tenant, user_is_tenant_staff


def is_teacher_or_staff(user, request=None):
    """Check if user is a teacher or staff member for the active tenant."""
    tenant = get_request_tenant(request) if request is not None else None
    if tenant is None:
        return user.groups.filter(name__in=['Teacher', 'Staff']).exists()
    return user_is_tenant_staff(user, tenant=tenant)


class TeacherQuestionBankListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all question banks created by the current teacher"""
    model = QuestionBank
    template_name = 'cbt/question_bank_list.html'
    context_object_name = 'question_banks'
    paginate_by = 20

    def test_func(self):
        return is_teacher_or_staff(self.request.user)

    def get_queryset(self):
        queryset = QuestionBank.objects.filter(
            created_by=self.request.user
        ).select_related('subject', 'school_class', 'term').annotate(question_count=Count('questions')).order_by('-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Filter by subject
        subject_id = self.request.GET.get('subject')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        
        # Filter by class
        class_id = self.request.GET.get('class')
        if class_id:
            queryset = queryset.filter(school_class_id=class_id)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subjects'] = Subject.objects.all()
        context['classes'] = SchoolClasses.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        context['total_banks'] = QuestionBank.objects.filter(created_by=self.request.user).count()
        context['total_questions'] = CBTQuestion.objects.filter(question_bank__created_by=self.request.user).count()
        context['recent_questions'] = CBTQuestion.objects.filter(question_bank__created_by=self.request.user).order_by('-created_at')[:5]
        return context


class QuestionBankCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new question bank"""
    model = QuestionBank
    form_class = QuestionBankForm
    template_name = 'cbt/question_bank_form.html'
    success_url = reverse_lazy('teacher_cbt:question_banks')

    def test_func(self):
        return is_teacher_or_staff(self.request.user)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Question Bank'
        return context


class QuestionBankUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update an existing question bank"""
    model = QuestionBank
    form_class = QuestionBankForm
    template_name = 'cbt/question_bank_form.html'
    success_url = reverse_lazy('teacher_cbt:question_banks')

    def test_func(self):
        question_bank = self.get_object()
        return question_bank.created_by == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Question Bank'
        return context


class QuestionBankDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a question bank"""
    model = QuestionBank
    template_name = 'cbt/question_bank_confirm_delete.html'
    success_url = reverse_lazy('teacher_cbt:question_banks')

    def test_func(self):
        question_bank = self.get_object()
        return question_bank.created_by == self.request.user


class QuestionBankDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View details of a question bank and manage its questions"""
    model = QuestionBank
    template_name = 'cbt/question_bank_detail.html'
    context_object_name = 'question_bank'

    def test_func(self):
        question_bank = self.get_object()
        return question_bank.created_by == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question_bank = self.get_object()
        
        # Get questions with search/filter
        questions = question_bank.questions.select_related('question_bank').prefetch_related('choices')
        
        search_query = self.request.GET.get('q')
        if search_query:
            questions = questions.filter(
                Q(prompt__icontains=search_query) |
                Q(topic__icontains=search_query) |
                Q(tags__icontains=search_query)
            )
        
        # Filter by difficulty
        difficulty = self.request.GET.get('difficulty')
        if difficulty:
            questions = questions.filter(difficulty=difficulty)
        
        # Filter by type
        question_type = self.request.GET.get('type')
        if question_type:
            questions = questions.filter(question_type=question_type)

        topic = self.request.GET.get('topic')
        if topic:
            questions = questions.filter(topic=topic)

        tags = self.request.GET.get('tags')
        if tags:
            questions = questions.filter(tags__icontains=tags)

        favorite_only = self.request.GET.get('favorite')
        if favorite_only == '1':
            questions = questions.filter(is_favorite=True)
        
        question_list = questions.order_by('order', '-created_at')
        question_topics = question_bank.questions.values_list('topic', flat=True).distinct().order_by('topic')
        question_tags = []
        for tag_list in question_bank.questions.values_list('tags', flat=True):
            if tag_list:
                for tag in [t.strip() for t in tag_list.split(',') if t.strip()]:
                    if tag not in question_tags:
                        question_tags.append(tag)
        
        context['questions'] = question_list
        context['question_count'] = question_bank.get_question_count()
        context['search_query'] = search_query or ''
        context['difficulties'] = CBTQuestion.DIFFICULTY_CHOICES
        context['question_types'] = CBTQuestion.QUESTION_TYPE_CHOICES
        context['question_topics'] = question_topics
        context['question_tags'] = question_tags
        context['favorite_questions'] = question_bank.questions.filter(is_favorite=True).order_by('-updated_at')[:5]
        context['recent_questions'] = question_bank.questions.order_by('-created_at')[:5]
        context['active_questions'] = question_bank.questions.filter(is_active=True).count()
        context['inactive_questions'] = question_bank.questions.filter(is_active=False).count()
        context['favorite_count'] = question_bank.questions.filter(is_favorite=True).count()
        context['used_questions'] = question_bank.questions.filter(exam__isnull=False).count()
        context['selected_tag'] = tags or ''
        context['selected_topic'] = topic or ''
        context['favorite_only'] = favorite_only == '1'
        
        return context


class QuestionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new question in a question bank"""
    model = CBTQuestion
    form_class = CBTQuestionForm
    template_name = 'cbt/question_form.html'

    def test_func(self):
        question_bank = get_object_or_404(QuestionBank, pk=self.kwargs['bank_pk'])
        return question_bank.created_by == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['question_bank'] = get_object_or_404(QuestionBank, pk=self.kwargs['bank_pk'])
        context['page_title'] = 'Add Question'
        
        if self.request.POST:
            context['choices_formset'] = CBTChoiceFormSet(self.request.POST, instance=self.object)
        else:
            context['choices_formset'] = CBTChoiceFormSet(instance=self.object)
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['choices_formset']
        
        if formset.is_valid():
            question_bank = get_object_or_404(QuestionBank, pk=self.kwargs['bank_pk'])
            form.instance.question_bank = question_bank
            form.instance.exam = None  # Not linked to exam yet
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            return redirect('teacher_cbt:question_bank_detail', pk=question_bank.pk)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('teacher_cbt:question_bank_detail', kwargs={'pk': self.kwargs['bank_pk']})


class QuestionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update an existing question"""
    model = CBTQuestion
    form_class = CBTQuestionForm
    template_name = 'cbt/question_form.html'

    def test_func(self):
        question = self.get_object()
        if question.question_bank:
            return question.question_bank.created_by == self.request.user
        elif question.exam:
            return question.exam.created_by == self.request.user
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question = self.get_object()
        context['question_bank'] = question.question_bank
        context['page_title'] = 'Edit Question'
        
        if self.request.POST:
            context['choices_formset'] = CBTChoiceFormSet(self.request.POST, instance=question)
        else:
            context['choices_formset'] = CBTChoiceFormSet(instance=question)
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['choices_formset']
        
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            if self.object.question_bank:
                return redirect('teacher_cbt:question_bank_detail', pk=self.object.question_bank.pk)
            else:
                return redirect('teacher_cbt:manage_questions', exam_pk=self.object.exam.pk)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        question = self.get_object()
        if question.question_bank:
            return reverse_lazy('teacher_cbt:question_bank_detail', kwargs={'pk': question.question_bank.pk})
        else:
            return reverse_lazy('teacher_cbt:manage_questions', kwargs={'exam_pk': question.exam.pk})


class QuestionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a question"""
    model = CBTQuestion
    template_name = 'cbt/question_confirm_delete.html'

    def test_func(self):
        question = self.get_object()
        if question.question_bank:
            return question.question_bank.created_by == self.request.user
        elif question.exam:
            return question.exam.created_by == self.request.user
        return False

    def get_success_url(self):
        question = self.get_object()
        if question.question_bank:
            return reverse_lazy('teacher_cbt:question_bank_detail', kwargs={'pk': question.question_bank.pk})
        else:
            return reverse_lazy('teacher_cbt:manage_questions', kwargs={'exam_pk': question.exam.pk})


class QuestionCloneView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Clone an existing question to create a new one"""
    model = CBTQuestion
    form_class = CBTQuestionForm
    template_name = 'cbt/question_form.html'

    def test_func(self):
        source_question = get_object_or_404(CBTQuestion, pk=self.kwargs['question_pk'])
        if source_question.question_bank:
            return source_question.question_bank.created_by == self.request.user
        return False

    def get_initial(self):
        source_question = get_object_or_404(CBTQuestion, pk=self.kwargs['question_pk'])
        return {
            'prompt': source_question.prompt,
            'question_type': source_question.question_type,
            'mark_value': source_question.mark_value,
            'explanation': source_question.explanation,
            'topic': source_question.topic,
            'tags': source_question.tags,
            'difficulty': source_question.difficulty,
            'is_favorite': source_question.is_favorite,
        }

    def form_valid(self, form):
        source_question = get_object_or_404(CBTQuestion, pk=self.kwargs['question_pk'])
        question_bank = source_question.question_bank
        
        context = self.get_context_data()
        formset = context['choices_formset']
        
        if formset.is_valid():
            form.instance.question_bank = question_bank
            form.instance.exam = None
            self.object = form.save()
            
            # Clone choices from source question
            for choice in source_question.choices.all():
                CBTChoice.objects.create(
                    question=self.object,
                    text=choice.text,
                    is_correct=choice.is_correct,
                    order=choice.order
                )
            
            formset.instance = self.object
            formset.save()
            return redirect('teacher_cbt:question_bank_detail', pk=question_bank.pk)
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        source_question = get_object_or_404(CBTQuestion, pk=self.kwargs['question_pk'])
        context['question_bank'] = source_question.question_bank
        context['page_title'] = 'Clone Question'
        context['source_question'] = source_question
        
        if self.request.POST:
            context['choices_formset'] = CBTChoiceFormSet(self.request.POST, instance=self.object)
        else:
            context['choices_formset'] = CBTChoiceFormSet(instance=self.object)
        
        return context

    def get_success_url(self):
        source_question = get_object_or_404(CBTQuestion, pk=self.kwargs['question_pk'])
        return reverse_lazy('teacher_cbt:question_bank_detail', kwargs={'pk': source_question.question_bank.pk})


class QuestionBankBulkActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Handle bulk actions for questions inside a question bank"""

    def test_func(self):
        question_bank = get_object_or_404(QuestionBank, pk=self.kwargs['pk'])
        return question_bank.created_by == self.request.user

    def post(self, request, *args, **kwargs):
        question_bank = get_object_or_404(QuestionBank, pk=self.kwargs['pk'], created_by=request.user)
        selected_ids = request.POST.getlist('selected_questions')
        action = request.POST.get('action')
        target_bank_id = request.POST.get('target_bank')

        if not selected_ids or not action:
            return redirect('teacher_cbt:question_bank_detail', pk=question_bank.pk)

        questions = question_bank.questions.filter(pk__in=selected_ids)

        if action == 'delete':
            questions.delete()
        elif action == 'activate':
            questions.update(is_active=True)
        elif action == 'deactivate':
            questions.update(is_active=False)
        elif action == 'favorite':
            questions.update(is_favorite=True)
        elif action == 'unfavorite':
            questions.update(is_favorite=False)
        elif action == 'duplicate':
            for question in questions:
                duplicate = CBTQuestion.objects.create(
                    exam=question.exam,
                    question_bank=question.question_bank,
                    prompt=question.prompt,
                    question_type=question.question_type,
                    mark_value=question.mark_value,
                    explanation=question.explanation,
                    topic=question.topic,
                    tags=question.tags,
                    difficulty=question.difficulty,
                    order=question.order + 1,
                    is_active=question.is_active,
                    is_favorite=question.is_favorite,
                )
                for choice in question.choices.all():
                    CBTChoice.objects.create(
                        question=duplicate,
                        text=choice.text,
                        is_correct=choice.is_correct,
                        order=choice.order,
                    )
        elif action == 'move' and target_bank_id:
            try:
                target_bank = QuestionBank.objects.get(pk=target_bank_id, created_by=request.user)
                questions.update(question_bank=target_bank)
            except QuestionBank.DoesNotExist:
                pass

        return redirect('teacher_cbt:question_bank_detail', pk=question_bank.pk)


class QuestionToggleFavoriteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Toggle favorite status for a question in a question bank"""

    def test_func(self):
        question = get_object_or_404(CBTQuestion, pk=self.kwargs['question_pk'])
        return question.question_bank and question.question_bank.created_by == self.request.user

    def post(self, request, *args, **kwargs):
        question = get_object_or_404(CBTQuestion, pk=self.kwargs['question_pk'])
        if not question.question_bank or question.question_bank.created_by != request.user:
            return HttpResponseForbidden()

        question.is_favorite = not question.is_favorite
        question.save(update_fields=['is_favorite'])

        return JsonResponse({
            'success': True,
            'is_favorite': question.is_favorite,
        })


class QuestionSearchAPIView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """API endpoint for searching questions in a question bank"""
    model = CBTQuestion
    
    def test_func(self):
        return is_teacher_or_staff(self.request.user)

    def get(self, request, *args, **kwargs):
        bank_id = request.GET.get('bank_id')
        search_query = request.GET.get('q', '')
        difficulty = request.GET.get('difficulty')
        topic = request.GET.get('topic')
        question_type = request.GET.get('type')
        
        if not bank_id:
            return JsonResponse({'error': 'bank_id required'}, status=400)
        
        question_bank = get_object_or_404(QuestionBank, pk=bank_id, created_by=request.user)
        
        questions = question_bank.questions.filter(is_active=True)
        
        if search_query:
            questions = questions.filter(
                Q(prompt__icontains=search_query) |
                Q(topic__icontains=search_query)
            )
        
        if difficulty:
            questions = questions.filter(difficulty=difficulty)
        
        if topic:
            questions = questions.filter(topic=topic)
        
        if question_type:
            questions = questions.filter(question_type=question_type)
        
        data = [
            {
                'id': q.id,
                'prompt': q.prompt[:100] + '...' if len(q.prompt) > 100 else q.prompt,
                'type': q.get_question_type_display(),
                'difficulty': q.get_difficulty_display(),
                'topic': q.topic,
                'mark_value': float(q.mark_value)
            }
            for q in questions.order_by('order')[:50]
        ]
        
        return JsonResponse({'questions': data})
