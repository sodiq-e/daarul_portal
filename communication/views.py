from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import MessageForm
from .models import Message
from settingsapp.email_service import send_contact_message_email, send_contact_message_confirmation_email


def user_is_teacher_or_admin(user):
    """Allow viewing contact messages for teachers and administrators."""
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    return user.groups.filter(name__in=['Teacher', 'Admin', 'Staff']).exists()


@login_required
def contact_message_list(request):
    if not user_is_teacher_or_admin(request.user):
        return HttpResponseForbidden('You do not have permission to view contact messages.')

    messages = Message.objects.order_by('-created_at')
    return render(request, 'communication/contact_message_list.html', {
        'messages': messages,
    })


def contact_view(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save()
            # Send email notification to admin
            send_contact_message_email(message)
            # Send confirmation email to sender
            send_contact_message_confirmation_email(message)
            return redirect('contact_success')
    else:
        form = MessageForm()

    return render(request, 'contact.html', {'form': form})


def contact_success(request):
    return render(request, 'contact_success.html')