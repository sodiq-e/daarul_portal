from .models import SchoolSettings, PageTheme, GalleryImage
from announcements.models import Announcement

def _get_page_key_from_path(path):
    """Determine which page the user is on based on the URL path"""
    path = path.lower()
    
    if path.startswith('/classes'):
        return 'classes'
    elif path.startswith('/results'):
        return 'results'
    elif path.startswith('/settings'):
        return 'settings'
    elif path.startswith('/students'):
        return 'students'
    elif path.startswith('/attendance'):
        return 'attendance'
    elif path.startswith('/exams'):
        return 'exams'
    elif path.startswith('/psychomotor'):
        return 'psychomotor'
    elif path.startswith('/payroll'):
        return 'payroll'
    else:
        return 'home'

def school_settings(request):
    """Context processor for school settings with defensive error handling"""
    try:
        settings = SchoolSettings.objects.first()
        
        # Get default theme colors from global settings
        default_theme = {
            "primary_color": settings.primary_color if settings else "#4b2e83",
            "secondary_color": settings.secondary_color if settings else "#7f5af0",
            "accent_color": settings.accent_color if settings else "#ffc107",
            "background_color": settings.background_color if settings else "#f5f5ff",
            "text_color": settings.text_color if settings else "#202040",
            "heading_text_color": settings.heading_text_color if settings else "#2a2a2a",
            "icon_plate_color": settings.icon_plate_color if settings else "#e8e0ff",
            "header_heading_color": settings.header_heading_color if settings else "#ffffff",
            "icon_color": settings.icon_color if settings else "#4b2e83",
        }
        
        # Check if current page has a custom theme
        page_key = _get_page_key_from_path(request.path)
        try:
            page_theme = PageTheme.objects.get(page_name=page_key, is_enabled=True)
            theme = {
                "primary_color": page_theme.primary_color,
                "secondary_color": page_theme.secondary_color,
                "accent_color": page_theme.accent_color,
                "background_color": page_theme.background_color,
                "text_color": page_theme.text_color,
                "heading_text_color": page_theme.heading_text_color,
                "icon_plate_color": page_theme.icon_plate_color,
                "header_heading_color": page_theme.header_heading_color,
                "icon_color": page_theme.icon_color,
            }
        except PageTheme.DoesNotExist:
            theme = default_theme

        return {
            "school_name": settings.school_name if settings else "School Name",
            "motto": settings.motto if settings else "",
            "school_logo": settings.logo.url if settings and settings.logo else None,
            "school_settings": settings,
            # Theme colors (uses page theme if exists, otherwise global theme)
            "primary_color": theme["primary_color"],
            "secondary_color": theme["secondary_color"],
            "accent_color": theme["accent_color"],
            "background_color": theme["background_color"],
            "text_color": theme["text_color"],
            "heading_text_color": theme["heading_text_color"],
            "icon_plate_color": theme["icon_plate_color"],
            "header_heading_color": theme["header_heading_color"],
            "icon_color": theme["icon_color"],
            # Also pass current page key for reference
            "current_page": page_key,
            # Gallery images
            "gallery_images": GalleryImage.objects.filter(school_settings=settings).order_by('order') if settings else [],
        }
    except Exception as e:
        # Log the error but don't crash the app
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error loading school settings context: {str(e)}")
        # Return safe defaults
        return {
            "school_name": "School Name",
            "motto": "",
            "school_logo": None,
            "school_settings": None,
            "primary_color": "#4b2e83",
            "secondary_color": "#7f5af0",
            "accent_color": "#ffc107",
            "background_color": "#f5f5ff",
            "text_color": "#202040",
            "heading_text_color": "#2a2a2a",
            "icon_plate_color": "#e8e0ff",
            "header_heading_color": "#ffffff",
            "icon_color": "#4b2e83",
            "current_page": "home",
            "gallery_images": [],
        }


def announcements_context(request):
    """Context processor for announcements"""
    try:
        active_announcements = Announcement.objects.filter(is_active=True)
        recent_announcements = active_announcements.order_by('-created_at')[:5]  # Last 5 announcements
        urgent_announcements = active_announcements.filter(priority='urgent')
        
        return {
            'active_announcements_count': active_announcements.count(),
            'recent_announcements': recent_announcements,
            'urgent_announcements_count': urgent_announcements.count(),
        }
    except Exception as e:
        # Log the error in production but don't crash the app
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error loading announcements context: {str(e)}")
        return {
            'active_announcements_count': 0,
            'recent_announcements': [],
            'urgent_announcements_count': 0,
        }
