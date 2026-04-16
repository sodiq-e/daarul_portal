from django.db import models

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

    logo = models.ImageField(
        upload_to='logos/',
        blank=True,
        null=True
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

    # Homepage content
    homepage_welcome_text = models.TextField(
        default="Welcome to the official digital platform of DAARUL BAYAAN ISLAMIC SCHOOL — a place designed to make learning, communication, and school management easier, faster, and more accessible for everyone. We provide a balanced education that combines Western and Islamic studies, including modern fields such as STEM and Robotics.",
        blank=True,
        help_text="Welcome text displayed on the homepage for visitors"
    )

    homepage_video_description = models.TextField(
        default="Replace this placeholder with your school introduction video. Edit the template at templates/home.html to add your video embed code.",
        blank=True,
        help_text="Description text for the video placeholder on homepage"
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
        upload_to='gallery/',
        help_text="Upload gallery image"
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
