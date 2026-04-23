from .models import Page


def navigation_pages(request):
    """
    Context processor that provides published pages grouped by url_prefix.
    
    Automatically includes all pages where:
    - is_published = True
    - show_in_navigation = True
    
    Returns grouped dictionary for template usage:
    {
        'navigation_pages_by_prefix': {
            'announcements': [page1, page2, ...],
            'classes': [page3, page4, ...],
        }
    }
    """
    try:
        # Fetch published navigation pages
        nav_pages = Page.objects.filter(
            is_published=True,
            show_in_navigation=True
        ).order_by('url_prefix', 'title')
        
        # Group by url_prefix
        pages_by_prefix = {}
        for page in nav_pages:
            prefix = page.url_prefix or 'general'
            if prefix not in pages_by_prefix:
                pages_by_prefix[prefix] = []
            pages_by_prefix[prefix].append(page)
        
        return {
            'navigation_pages_by_prefix': pages_by_prefix,
        }
    except Exception:
        # Gracefully handle if Page model doesn't exist or during initial migrations
        return {
            'navigation_pages_by_prefix': {},
        }
