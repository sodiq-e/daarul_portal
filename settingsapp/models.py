from django.db import models
#from cloudinary.models import CloudinaryField

class SchoolSettings(models.Model):
    school_name = models.CharField(
        max_length=200,
        default="Daarul Bayaan Islamic School",
        blank=True,
        null=True
    )

    motto = models.CharField(
        max_length=255,
        default="Knowledge for the Fear of God",
        blank=True,
        null=True
    )

    # logo = CloudinaryField(
    #     'image',
    #     folder='logos',
    #     blank=True,
    #     null=True
    # )
    logo = models.ImageField(
    upload_to='logos/',
    blank=True,
    null=True
    )
    primary_color = models.CharField(
        max_length=7,
        default="#4b2e83",
        help_text="Primary color for header and accents (hex format)"
    )

    secondary_color = models.CharField(
        max_length=7,
        default="#7f5af0",
        help_text="Secondary color for gradients (hex format)"
    )

    accent_color = models.CharField(
        max_length=7,
        default="#ffc107",
        help_text="Accent color for buttons and highlights (hex format)"
    )

    background_color = models.CharField(
        max_length=7,
        default="#f5f5ff",
        help_text="Background color (hex format)"
    )

    text_color = models.CharField(
        max_length=7,
        default="#202040",
        help_text="Main text color (hex format)"
    )

    heading_text_color = models.CharField(
        max_length=7,
        default="#2a2a2a",
        help_text="Heading text color (hex format)"
    )

    icon_plate_color = models.CharField(
        max_length=7,
        default="#e8e0ff",
        help_text="Icon plate/background color (hex format)"
    )

    header_heading_color = models.CharField(
        max_length=7,
        default="#ffffff",
        help_text="Header heading/school name color (hex format)"
    )

    icon_color = models.CharField(
        max_length=7,
        default="#4b2e83",
        help_text="Icon/emoji color (hex format)"
    )

    # Homepage content
    homepage_hero_enabled = models.BooleanField(
        default=True,
        help_text="Enable or disable the modern homepage hero section for visitors"
    )

    homepage_hero_slide_duration = models.PositiveIntegerField(
        default=6500,
        help_text="Hero background slide duration in milliseconds"
    )

    homepage_hero_show_announcements = models.BooleanField(
        default=True,
        help_text="Show announcement preview inside the homepage hero"
    )

    homepage_hero_show_counters = models.BooleanField(
        default=True,
        help_text="Display counts for announcements and gallery highlights in the homepage hero"
    )

    homepage_welcome_text = models.TextField(
        default="Welcome to the official digital platform of DAARUL BAYAAN ISLAMIC SCHOOL — a place designed to make learning, communication, and school management easier, faster, and more accessible for everyone. We provide a balanced education that combines Western and Islamic studies, including modern fields such as STEM and Robotics.",
        blank=True,
        help_text="Welcome text displayed on the homepage for visitors"
    )

    hero_title_font_size = models.CharField(
        max_length=30,
        default='clamp(2.5rem, 4.8vw, 4.3rem)',
        blank=True,
        help_text='CSS font size for the hero title (e.g. 3rem or clamp(...))'
    )

    hero_intro_font_size = models.CharField(
        max_length=30,
        default='clamp(0.95rem, 1.35vw, 1.05rem)',
        blank=True,
        help_text='CSS font size for the hero intro / supporting text'
    )

    hero_rotator_title_font_size = models.CharField(
        max_length=30,
        default='clamp(1.25rem, 2.2vw, 1.75rem)',
        blank=True,
        help_text='CSS font size for rotating hero text titles'
    )

    hero_rotator_subtitle_font_size = models.CharField(
        max_length=30,
        default='clamp(0.95rem, 1.4vw, 1.05rem)',
        blank=True,
        help_text='CSS font size for rotating hero subtitles'
    )

    hero_title_color = models.CharField(
        max_length=7,
        default='#ffffff',
        blank=True,
        help_text='Text color for the hero title'
    )

    hero_text_color = models.CharField(
        max_length=7,
        default='#f5f7ff',
        blank=True,
        help_text='Text color for hero intro and supporting copy'
    )

    hero_button_font_size = models.CharField(
        max_length=20,
        default='0.82rem',
        blank=True,
        help_text='CSS font size for hero buttons'
    )

    hero_button_text_color = models.CharField(
        max_length=7,
        default='#ffffff',
        blank=True,
        help_text='Text color for hero CTA buttons'
    )

    hero_button_background_color = models.CharField(
        max_length=7,
        default='#4b2e83',
        blank=True,
        help_text='Background color for hero CTA buttons'
    )

    hero_button_border_color = models.CharField(
        max_length=7,
        default='#ffffff',
        blank=True,
        help_text='Border color for hero CTA buttons'
    )

    hero_button_hover_background_color = models.CharField(
        max_length=7,
        default='#ffffff',
        blank=True,
        help_text='Hover background color for hero CTA buttons'
    )

    hero_button_hover_text_color = models.CharField(
        max_length=7,
        default='#4b2e83',
        blank=True,
        help_text='Hover text color for hero CTA buttons'
    )

    homepage_hero_eyebrow = models.CharField(
        max_length=80,
        default="Welcome to",
        blank=True,
        help_text="Short label above the hero heading"
    )

    homepage_hero_title = models.CharField(
        max_length=160,
        default="A premium school experience rooted in excellence",
        blank=True,
        help_text="Main heading displayed in the homepage hero"
    )

    homepage_hero_intro = models.TextField(
        default="A nurturing and modern learning environment for students, families, and staff.",
        blank=True,
        help_text="Supporting copy shown beneath the hero title"
    )

    homepage_hero_primary_cta_label = models.CharField(
        max_length=60,
        default="Apply for Admission",
        blank=True,
        help_text="Primary CTA label in the hero"
    )

    homepage_hero_secondary_cta_label = models.CharField(
        max_length=60,
        default="Contact Us",
        blank=True,
        help_text="Secondary CTA label in the hero"
    )

    homepage_hero_tertiary_cta_label = models.CharField(
        max_length=60,
        default="View Gallery",
        blank=True,
        help_text="Tertiary CTA label in the hero"
    )

    homepage_hero_announcements_label = models.CharField(
        max_length=80,
        default="Latest Announcement",
        blank=True,
        help_text="Label shown above the announcement preview in the hero"
    )

    homepage_hero_stat_announcements_label = models.CharField(
        max_length=40,
        default="Announcements",
        blank=True,
        help_text="Label for the announcements hero stat card"
    )

    homepage_hero_stat_gallery_label = models.CharField(
        max_length=40,
        default="Gallery",
        blank=True,
        help_text="Label for the gallery hero stat card"
    )

    homepage_hero_stat_students_label = models.CharField(
        max_length=40,
        default="Students",
        blank=True,
        help_text="Label for the students hero stat card"
    )

    homepage_hero_stat_teachers_label = models.CharField(
        max_length=40,
        default="Teachers",
        blank=True,
        help_text="Label for the teachers hero stat card"
    )

    homepage_updates_title = models.CharField(
        max_length=120,
        default="Latest Updates",
        blank=True,
        help_text="Title shown for the latest updates section"
    )

    homepage_updates_empty_text = models.CharField(
        max_length=200,
        default="No updates available yet.",
        blank=True,
        help_text="Message shown when no updates are available"
    )

    homepage_overview_title = models.CharField(
        max_length=140,
        default="What You Can Do on This Portal",
        blank=True,
        help_text="Heading for the overview cards section"
    )

    homepage_overview_intro = models.TextField(
        default="Explore a secure digital experience designed to keep students, families, and staff connected.",
        blank=True,
        help_text="Intro paragraph shown above the overview cards"
    )

    homepage_overview_card_1_title = models.CharField(
        max_length=120,
        default="Access academic records",
        blank=True,
        help_text="Title for the first overview card"
    )

    homepage_overview_card_1_description = models.TextField(
        default="View your results, grades, and progress reports from one secure location.",
        blank=True,
        help_text="Description for the first overview card"
    )

    homepage_overview_card_2_title = models.CharField(
        max_length=120,
        default="View class schedules",
        blank=True,
        help_text="Title for the second overview card"
    )

    homepage_overview_card_2_description = models.TextField(
        default="Check timetables, subject details, and classroom assignments at a glance.",
        blank=True,
        help_text="Description for the second overview card"
    )

    homepage_overview_card_3_title = models.CharField(
        max_length=120,
        default="Receive school updates",
        blank=True,
        help_text="Title for the third overview card"
    )

    homepage_overview_card_3_description = models.TextField(
        default="Stay informed with announcements, news, and important school events.",
        blank=True,
        help_text="Description for the third overview card"
    )

    homepage_overview_card_4_title = models.CharField(
        max_length=120,
        default="Communicate easily",
        blank=True,
        help_text="Title for the fourth overview card"
    )

    homepage_overview_card_4_description = models.TextField(
        default="Message teachers and school management through the portal's secure channels.",
        blank=True,
        help_text="Description for the fourth overview card"
    )

    homepage_overview_card_5_title = models.CharField(
        max_length=120,
        default="Manage your profile",
        blank=True,
        help_text="Title for the fifth overview card"
    )

    homepage_overview_card_5_description = models.TextField(
        default="Update your account information and keep your profile current.",
        blank=True,
        help_text="Description for the fifth overview card"
    )

    homepage_important_notice_title = models.CharField(
        max_length=120,
        default="Important Notice",
        blank=True,
        help_text="Title for the important notice section"
    )

    homepage_important_notice_text = models.TextField(
        default="Your login details are personal and should not be shared with anyone. Keep your credentials safe to protect your academic information.",
        blank=True,
        help_text="Body text for the important notice section"
    )

    homepage_help_title = models.CharField(
        max_length=120,
        default="Need Help?",
        blank=True,
        help_text="Title for the help section"
    )

    homepage_help_text = models.TextField(
        default="If you experience any difficulty accessing your account or navigating the portal, please contact the school administration for assistance.",
        blank=True,
        help_text="Body text for the help section"
    )

    homepage_gallery_title = models.CharField(
        max_length=120,
        default="Portal Gallery",
        blank=True,
        help_text="Title for the gallery section"
    )

    homepage_gallery_description = models.TextField(
        default="Browse highlights from the portal and explore the types of information available.",
        blank=True,
        help_text="Description for the gallery section"
    )

    homepage_video_description = models.TextField(
        default="Replace this placeholder with your school introduction video. Edit the template at templates/home.html to add your video embed code.",
        blank=True,
        help_text="Description text for the video placeholder on homepage"
    )
    # homepage_video = CloudinaryField(
    #     'videos',
    #     folder='videos',
    #     blank=True,
    #     null=True
    # )

    homepage_video = models.FileField(
    upload_to='videos/',
    blank=True,
    null=True
    )
    homepage_video_url = models.URLField(
        blank=True,
        null=True
    )

    # Email Notification Settings
    admin_email = models.EmailField(
        default='daarulbayaanis@gmail.com',
        help_text="Primary email address for receiving notifications (account creation, contact messages, etc.)"
    )

    admin_email_cc = models.CharField(
        max_length=500,
        blank=True,
        help_text="Additional email addresses to CC on notifications (comma-separated)"
    )

    send_account_creation_email = models.BooleanField(
        default=True,
        help_text="Send email notification when new accounts are created"
    )

    send_contact_message_email = models.BooleanField(
        default=True,
        help_text="Send email notification when contact form messages are submitted"
    )

    send_application_email = models.BooleanField(
        default=True,
        help_text="Send email notification when applications/forms are submitted"
    )

    account_creation_email_subject = models.CharField(
        max_length=200,
        default="New Account Created - {school_name}",
        help_text="Email subject for account creation. Use {school_name} as placeholder"
    )

    contact_message_email_subject = models.CharField(
        max_length=200,
        default="New Contact Message - {school_name}",
        help_text="Email subject for contact messages. Use {school_name} as placeholder"
    )

    application_email_subject = models.CharField(
        max_length=200,
        default="New Application Received - {school_name}",
        help_text="Email subject for applications. Use {school_name} as placeholder"
    )

    # School Contact Information (for header/documents)
    school_address = models.TextField(
        default="123 Main Street, City, Country",
        blank=True,
        null=True,
        help_text="School physical address displayed in header and documents"
    )

    school_phone = models.CharField(
        max_length=255,
        default="+234 (0) 123 456 7890",
        blank=True,
        null=True,
        help_text="School contact phone number"
    )

    school_email = models.EmailField(
        default="info@daarulbayaan.edu",
        blank=True,
        null=True,
        help_text="School general contact email address"
    )

    # Footer Copyright
    footer_copyright_text = models.CharField(
        max_length=500,
        default="© 2026 Daarul Bayaan Islamic School. All Rights Reserved.",
        blank=True,
        help_text="Copyright text displayed in footer"
    )

    footer_copyright_link = models.URLField(
        blank=True,
        null=True,
        help_text="Optional link for copyright (e.g., privacy policy URL)"
    )

    def __str__(self):
        return self.school_name or "School Settings"


class PageTheme(models.Model):
    """Define custom theme for specific pages/routes"""

    # Predefined common pages
    PREDEFINED_PAGES = [
        ('home', 'Home Page'),
        ('classes', 'Classes Page'),
        ('results', 'Results Page'),
        ('settings', 'Settings Page'),
        ('students', 'Students Page'),
        ('attendance', 'Attendance Page'),
        ('exams', 'Exams Page'),
        ('psychomotor', 'Psychomotor Page'),
        ('payroll', 'Payroll Page'),
    ]

    page_name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Enter page name (e.g., 'home', 'classes', 'announcements'). Use lowercase with underscores for spaces."
    )

    page_display_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Display name for this page (optional, e.g., 'Home Page', 'Custom Reports')"
    )

    url_pattern = models.CharField(
        max_length=100,
        blank=True,
        help_text="URL path to match (e.g., '/classes/', '/announcements/'). Leave blank for automatic detection."
    )

    is_enabled = models.BooleanField(
        default=True,
        help_text="Enable or disable this page theme"
    )

    # Theme colors
    primary_color = models.CharField(
        max_length=7,
        default="#4b2e83",
        help_text="Primary color for header and accents (hex format)"
    )

    secondary_color = models.CharField(
        max_length=7,
        default="#7f5af0",
        help_text="Secondary color for gradients (hex format)"
    )

    accent_color = models.CharField(
        max_length=7,
        default="#ffc107",
        help_text="Accent color for buttons and highlights (hex format)"
    )

    background_color = models.CharField(
        max_length=7,
        default="#f5f5ff",
        help_text="Background color (hex format)"
    )

    text_color = models.CharField(
        max_length=7,
        default="#202040",
        help_text="Main text color (hex format)"
    )

    heading_text_color = models.CharField(
        max_length=7,
        default="#2a2a2a",
        help_text="Heading text color (hex format)"
    )

    icon_plate_color = models.CharField(
        max_length=7,
        default="#e8e0ff",
        help_text="Icon plate/background color (hex format)"
    )

    header_heading_color = models.CharField(
        max_length=7,
        default="#ffffff",
        help_text="Header heading/school name color (hex format)"
    )

    icon_color = models.CharField(
        max_length=7,
        default="#4b2e83",
        help_text="Icon/emoji color (hex format)"
    )

    class Meta:
        ordering = ['page_name']
        verbose_name_plural = "Page Themes"

    def __str__(self):
        return self.page_display_name or f"{self.page_name.title()} Theme"

    @classmethod
    def get_predefined_pages(cls):
        """Get list of predefined pages"""
        return cls.PREDEFINED_PAGES


class GalleryImage(models.Model):
    """Gallery images for the school portal"""

    school_settings = models.ForeignKey(
        SchoolSettings,
        on_delete=models.CASCADE,
        related_name='gallery_images'
    )

    image = models.ImageField(
    upload_to='gallery/images/',
    blank=True,
    null=True,
    help_text="Upload image (optional)"
    )

    video = models.FileField(
    upload_to='gallery/videos/',
    blank=True,
    null=True,
    help_text="Upload video (optional)"
    )
    homepage_video_url = models.URLField(
        blank=True,
        null=True,
        help_text="Paste YouTube embed link (https://www.youtube.com/embed/...)"
    )
    USAGE_GALLERY = 'gallery'
    USAGE_HERO = 'hero'
    USAGE_PORTAL_VIDEO = 'portal_video'
    USAGE_CHOICES = [
        (USAGE_GALLERY, 'Gallery'),
        (USAGE_HERO, 'Hero (Homepage)'),
        (USAGE_PORTAL_VIDEO, 'Portal Video')
    ]

    usage = models.CharField(
        max_length=20,
        choices=USAGE_CHOICES,
        default=USAGE_GALLERY,
        help_text="How this media item is used on the site. 'Hero' images appear in the homepage hero."
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Image title or caption (optional)"
    )

    description = models.TextField(
        blank=True,
        help_text="Image description (optional)"
    )

    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order in gallery"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name_plural = "Gallery Images"

    def __str__(self):
        return self.title or f"Gallery Image - {self.created_at.strftime('%Y-%m-%d')}"


class HeroText(models.Model):
    """Animated hero text entries managed in Portal Settings"""

    ANIMATION_CHOICES = [
        ('fade', 'Fade'),
        ('slide', 'Slide'),
        ('zoom', 'Zoom'),
        ('typing', 'Typing'),
        ('float', 'Float'),
    ]

    school_settings = models.ForeignKey(
        SchoolSettings,
        on_delete=models.CASCADE,
        related_name='hero_texts'
    )

    title = models.CharField(max_length=300, blank=True)
    subtitle = models.CharField(max_length=300, blank=True)
    button_text = models.CharField(max_length=120, blank=True)
    button_url = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    animation_type = models.CharField(max_length=32, default='fade', choices=ANIMATION_CHOICES, help_text="Main motion style")
    animation_styles = models.CharField(
        max_length=200,
        default='fade,slide',
        blank=True,
        help_text="Extra motion styles to rotate through, for example: fade, slide, typing"
    )
    display_seconds = models.PositiveIntegerField(default=4)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.title or (self.subtitle or 'Hero Text')


class HeroButton(models.Model):
    """Custom CTA buttons shown in the hero, controlled via settings"""

    school_settings = models.ForeignKey(
        SchoolSettings,
        on_delete=models.CASCADE,
        related_name='hero_buttons'
    )

    label = models.CharField(max_length=120)
    url = models.CharField(max_length=500, blank=True, default='')
    order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    open_in_new_tab = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.label


# Additional hero configuration fields on SchoolSettings
SchoolSettings.add_to_class('hero_height', models.CharField(max_length=20, default='80vh', blank=True, help_text='CSS height value for the hero (e.g., 80vh, 600px)'))
SchoolSettings.add_to_class('hero_overlay_opacity', models.PositiveSmallIntegerField(default=50, help_text='Overlay opacity percentage (0-100)'))
SchoolSettings.add_to_class('hero_text_position', models.CharField(max_length=10, default='left', choices=[('left','Left'),('center','Center'),('right','Right')], help_text='Position of hero text'))
SchoolSettings.add_to_class('hero_animation_speed', models.PositiveIntegerField(default=900, help_text='Animation speed in milliseconds for text transitions'))
SchoolSettings.add_to_class('enable_auto_slide', models.BooleanField(default=True))
SchoolSettings.add_to_class('enable_hero_overlay', models.BooleanField(default=True))
SchoolSettings.add_to_class('enable_hero_text_animation', models.BooleanField(default=True))
