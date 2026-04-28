from django.shortcuts import render, redirect
from .forms import MessageForm
from settingsapp.email_service import send_contact_message_email


def contact_view(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save()
            # Send email notification
            send_contact_message_email(message)
            return redirect('contact_success')
    else:
        form = MessageForm()

    return render(request, 'contact.html', {'form': form})


def contact_success(request):
    return render(request, 'contact_success.html')