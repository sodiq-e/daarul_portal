from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from .models import SchoolClasses


@method_decorator(login_required, name='dispatch')
class ClassListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = SchoolClasses
    template_name = 'classes/class_list.html'
    context_object_name = 'classes'

    def test_func(self):
        return self.request.user.profile.is_approved

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = (
            self.request.user.profile.is_approved and
            self.request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()
        )
        return context


@login_required
def add_class(request):
    if not (request.user.profile.is_approved and request.user.groups.filter(name__in=['Teacher', 'Staff']).exists()):
        from django.contrib import messages
        messages.error(request, 'You do not have permission to add classes.')
        return redirect('class_list')

    if request.method == 'POST':
        name = request.POST.get('class_name')
        level = request.POST.get('level')
        desc = request.POST.get('description')

        # Prevent empty class name
        if name:
            try:
                SchoolClasses.objects.create(
                    class_name=name,
                    level=level,
                    description=desc
                )
            except:
                # Handles duplicate class_name (unique=True)
                pass

        return redirect('class_list')

    return render(request, 'classes/add_class.html')
