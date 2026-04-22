from django import forms
from .models import SchoolSettings, PageTheme, GalleryImage

class SchoolSettingsForm(forms.ModelForm):
    primary_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)
    secondary_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)
    accent_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)
    background_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)
    text_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)
    heading_text_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)
    icon_plate_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)
    header_heading_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)
    icon_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)

    class Meta:
        model = SchoolSettings
        fields = [
            'school_name',
            'motto',
            'logo',
            'primary_color',
            'secondary_color',
            'accent_color',
            'background_color',
            'text_color',
            'heading_text_color',
            'icon_plate_color',
            'header_heading_color',
            'icon_color',
            'homepage_video',
            'homepage_video_url',
            'homepage_video_description',

        ]


class PageThemeForm(forms.ModelForm):
    primary_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)
    secondary_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)
    accent_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)
    background_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)
    text_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)
    heading_text_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)
    icon_plate_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)
    header_heading_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)
    icon_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=True)

    class Meta:
        model = PageTheme
        fields = [
            'page_name',
            'page_display_name',
            'url_pattern',
            'is_enabled',
            'primary_color',
            'secondary_color',
            'accent_color',
            'background_color',
            'text_color',
            'heading_text_color',
            'icon_plate_color',
            'header_heading_color',
            'icon_color'
        ]
        help_texts = {
            'page_name': 'Use lowercase with underscores (e.g., "announcements", "library")',
            'page_display_name': 'Optional: Display name for this page',
            'url_pattern': 'Optional: URL path to match (e.g., "/announcements/")'
        }


class GalleryImageForm(forms.ModelForm):

    class Meta:
        model = GalleryImage
        fields = ['image', 'video', 'title', 'description', 'order']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'gallery-image-input',
                'accept': 'image/*'
            }),
            'video': forms.FileInput(attrs={
                'class': 'gallery-video-input',
                'accept': 'video/*'
            }),
            'title': forms.TextInput(attrs={
                'placeholder': 'Title (optional)',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Description (optional)',
                'class': 'form-control'
            }),
            'order': forms.NumberInput(attrs={
                'value': 0,
                'class': 'form-control'
            })
        }



GalleryImageFormSet = forms.modelformset_factory(
    GalleryImage,
    form=GalleryImageForm,
    extra=3,
    can_delete=True
)