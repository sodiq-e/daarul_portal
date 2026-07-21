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

    hero_title_font_size = forms.ChoiceField(
        choices=[
            ('clamp(2.5rem, 4.8vw, 4.3rem)', 'Large'),
            ('clamp(2.0rem, 3.6vw, 3.2rem)', 'Medium'),
            ('clamp(1.7rem, 3.0vw, 2.5rem)', 'Small'),
        ],
        required=False,
        label='Main Heading Size',
    )
    hero_intro_font_size = forms.ChoiceField(
        choices=[
            ('clamp(0.95rem, 1.35vw, 1.05rem)', 'Medium'),
            ('clamp(0.9rem, 1.2vw, 0.95rem)', 'Small'),
            ('clamp(1.05rem, 1.5vw, 1.15rem)', 'Large'),
        ],
        required=False,
        label='Intro Text Size',
    )
    hero_rotator_title_font_size = forms.ChoiceField(
        choices=[
            ('clamp(1.25rem, 2.2vw, 1.75rem)', 'Medium'),
            ('clamp(1.1rem, 1.9vw, 1.45rem)', 'Small'),
            ('clamp(1.45rem, 2.5vw, 2rem)', 'Large'),
        ],
        required=False,
        label='Animated Text Size',
    )
    hero_rotator_subtitle_font_size = forms.ChoiceField(
        choices=[
            ('clamp(0.95rem, 1.4vw, 1.05rem)', 'Medium'),
            ('clamp(0.85rem, 1.2vw, 0.95rem)', 'Small'),
            ('clamp(1.05rem, 1.6vw, 1.15rem)', 'Large'),
        ],
        required=False,
        label='Animated Detail Size',
    )
    hero_button_font_size = forms.ChoiceField(
        choices=[
            ('0.82rem', 'Medium'),
            ('0.75rem', 'Small'),
            ('0.95rem', 'Large'),
        ],
        required=False,
        label='Button Text Size',
    )
    hero_title_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=False, label='Main Heading Color')
    hero_text_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=False, label='Body Text Color')
    hero_button_text_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=False, label='Button Text Color')
    hero_button_background_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=False, label='Button Fill Color')
    hero_button_border_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=False, label='Button Border Color')
    hero_button_hover_background_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=False, label='Button Hover Fill')
    hero_button_hover_text_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=False, label='Button Hover Text')
    homepage_hero_primary_cta_label = forms.CharField(required=False, label='Primary CTA Label', widget=forms.TextInput(attrs={'placeholder': 'Apply Now'}), help_text='Example: Apply Now')

    class Meta:
        model = SchoolSettings
        fields = [
            'school_name',
            'motto',
            'logo',
            'school_address',
            'school_phone',
            'school_email',
            'primary_color',
            'secondary_color',
            'accent_color',
            'background_color',
            'text_color',
            'heading_text_color',
            'icon_plate_color',
            'header_heading_color',
            'icon_color',
            'homepage_hero_enabled',
            'homepage_hero_slide_duration',
            'homepage_hero_show_announcements',
            'homepage_hero_show_counters',
            'hero_title_font_size',
            'hero_intro_font_size',
            'hero_rotator_title_font_size',
            'hero_rotator_subtitle_font_size',
            'hero_title_color',
            'hero_text_color',
            'hero_button_font_size',
            'hero_button_text_color',
            'hero_button_background_color',
            'hero_button_border_color',
            'hero_button_hover_background_color',
            'hero_button_hover_text_color',
            'homepage_hero_eyebrow',
            'homepage_hero_title',
            'homepage_hero_intro',
            'homepage_hero_primary_cta_label',
            'homepage_hero_secondary_cta_label',
            'homepage_hero_tertiary_cta_label',
            'homepage_hero_announcements_label',
            'homepage_hero_stat_announcements_label',
            'homepage_hero_stat_gallery_label',
            'homepage_hero_stat_students_label',
            'homepage_hero_stat_teachers_label',
            'homepage_updates_title',
            'homepage_updates_empty_text',
            'homepage_overview_title',
            'homepage_overview_intro',
            'homepage_overview_card_1_title',
            'homepage_overview_card_1_description',
            'homepage_overview_card_2_title',
            'homepage_overview_card_2_description',
            'homepage_overview_card_3_title',
            'homepage_overview_card_3_description',
            'homepage_overview_card_4_title',
            'homepage_overview_card_4_description',
            'homepage_overview_card_5_title',
            'homepage_overview_card_5_description',
            'homepage_important_notice_title',
            'homepage_important_notice_text',
            'homepage_help_title',
            'homepage_help_text',
            'homepage_gallery_title',
            'homepage_gallery_description',
                'hero_height',
                'hero_overlay_opacity',
                'hero_text_position',
                'hero_animation_speed',
                'enable_auto_slide',
                'enable_hero_overlay',
                'enable_hero_text_animation',
            'homepage_video',
            'homepage_video_url',
            'homepage_video_description',
            'footer_copyright_text',
            'footer_copyright_link',
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
        fields = ['image', 'video', 'title', 'description', 'order', 'usage']
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


from .models import HeroText, HeroButton


class HeroTextForm(forms.ModelForm):
    class Meta:
        model = HeroText
        fields = ['title', 'subtitle', 'button_text', 'button_url', 'order', 'active', 'animation_type', 'animation_styles', 'display_seconds']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Main heading (optional)'}),
            'subtitle': forms.TextInput(attrs={'placeholder': 'Smaller subtitle (optional)'}),
            'button_text': forms.TextInput(attrs={'placeholder': 'Button text (optional)'}),
            'button_url': forms.TextInput(attrs={'placeholder': '/apply/ or https://example.com'}),
            'animation_styles': forms.TextInput(attrs={'placeholder': 'fade, slide, typing'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'value': 0}),
        }


class HeroButtonForm(forms.ModelForm):
    class Meta:
        model = HeroButton
        fields = ['label', 'url', 'order', 'active', 'open_in_new_tab']
        widgets = {
            'label': forms.TextInput(attrs={'placeholder': 'Button label'}),
            'url': forms.TextInput(attrs={'placeholder': '/apply/ or https://example.com'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'value': 0}),
        }


HeroTextFormSet = forms.modelformset_factory(HeroText, form=HeroTextForm, extra=2, can_delete=True)
HeroButtonFormSet = forms.modelformset_factory(HeroButton, form=HeroButtonForm, extra=3, can_delete=True)