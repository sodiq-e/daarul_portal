from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.forms import PasswordResetForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.generic import FormView
from django.contrib.auth.forms import AuthenticationForm
from .forms import StudentSignUpForm, UserProfileForm
from .models import Profile


@login_required
def user_profile(request):
    """User profile page"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


@require_http_methods(["GET", "POST"])
def student_signup(request):
    """Student sign up view"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Welcome {user.username}! Your account has been created successfully and is pending admin approval.'
            )
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = StudentSignUpForm()

    return render(request, 'accounts/signup.html', {'form': form})


class StudentPasswordResetView(PasswordResetView):
    """Custom password reset view for students"""
    form_class = PasswordResetForm
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')


class StudentPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view"""
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


def password_reset_done(request):
    """Password reset done page"""
    return render(request, 'accounts/password_reset_done.html')


def password_reset_complete(request):
    """Password reset complete page"""
    return render(request, 'accounts/password_reset_complete.html')


class CustomLoginView(FormView):
    """Custom login view that checks user approval status"""
    form_class = AuthenticationForm
    template_name = 'accounts/login.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                # Check if user is approved
                try:
                    profile = user.profile
                    if profile.is_approved:
                        login(self.request, user)
                        messages.success(self.request, f'Welcome back, {user.username}!')
                        return super().form_valid(form)
                    else:
                        messages.error(
                            self.request,
                            'Your account is pending admin approval. Please wait for an administrator to review and approve your registration.'
                        )
                        return self.form_invalid(form)
                except Profile.DoesNotExist:
                    messages.error(self.request, 'Your profile is not set up properly. Please contact an administrator.')
                    return self.form_invalid(form)
            else:
                messages.error(self.request, 'Your account is inactive. Please contact an administrator.')
                return self.form_invalid(form)
        else:
            messages.error(self.request, 'Invalid username or password.')
            return self.form_invalid(form)
