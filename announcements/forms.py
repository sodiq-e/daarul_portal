from django import forms
from .models import Announcement, AnnouncementCategory
from settingsapp.models import GalleryImage
from ckeditor.widgets import CKEditorWidget


class AnnouncementForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget(config_name='default'))
    galleries = forms.ModelMultipleChoiceField(
        queryset=GalleryImage.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6})
    )

    class Meta:
        model = Announcement
        fields = [
            'title', 'title_size', 'title_alignment', 'excerpt', 'content', 'category', 'featured_image',
            'video_thumbnail', 'video_url', 'galleries', 'priority', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'title_size': forms.Select(attrs={'class': 'form-select'}),
            'title_alignment': forms.Select(attrs={'class': 'form-select'}),
            'excerpt': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'featured_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'video_thumbnail': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_excerpt(self):
        data = self.cleaned_data.get('excerpt') or ''
        return data.strip()

    def clean(self):
        cleaned = super().clean()
        # If video_url provided ensure there is a thumbnail or featured image
        video = cleaned.get('video_url')
        thumb = cleaned.get('video_thumbnail')
        if video and not thumb and not cleaned.get('featured_image'):
            self.add_error('video_thumbnail', 'Please provide a thumbnail or featured image for the video.')
        return cleaned
