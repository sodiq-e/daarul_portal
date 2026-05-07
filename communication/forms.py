from django import forms
from .models import Message


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['name', 'email', 'phone', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4})
        }


class PortalMessageForm(forms.Form):
    content = forms.CharField(
        label='Message',
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'Write your message here...'
        })
    )
