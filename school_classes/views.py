from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.contrib import messages
from .models import SchoolClasses


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


@method_decorator(login_required, name='dispatch')
class ClassListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = SchoolClasses
    template_name = 'classes/class_list.html'
    context_object_name = 'classes'

    def test_func(self):
        return user_profile_approved(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = user_is_staff(self.request.user)
        return context


@login_required
def add_class(request):
    if not user_is_staff(request.user):
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
