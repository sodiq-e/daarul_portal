from django import forms
from .models import Message, PortalMessage


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['name', 'email', 'phone', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4})
        }


class PortalMessageForm(forms.ModelForm):
    class Meta:
        model = PortalMessage
        fields = ['content', 'attachment']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Write your message here...'
            })
        }
