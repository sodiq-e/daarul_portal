from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.apps import apps
from .models import Page


def page_view(request, slug):
    """
    Dynamic page view that renders pages based on slug.
    
    - Fetches only published pages
    - Dynamically handles different page types (normal, messages, news)
    - Fetches related PageContent entries if they exist
    - Gracefully falls back if related models don't exist
    - Renders custom templates per page
    """
    
    # Fetch only published pages
    page = get_object_or_404(Page, slug=slug, is_published=True)
    
    # Prepare context
    context = {
        'page': page,
    }
    
    # Fetch related PageContent entries
    # These are automatically included via the 'contents' related_name
    contents = page.contents.filter(is_published=True).order_by('order')
    if contents.exists():
        context['contents'] = contents
    
    # Handle dynamic page types with fallback logic
    if page.page_type == 'messages':
        # Try to fetch messages if model exists
        try:
            Message = apps.get_model('announcements', 'Message')
            context['messages'] = Message.objects.filter(is_active=True).order_by('-created_at')
        except LookupError:
            # Model doesn't exist - silently skip
            context['messages'] = []
    
    elif page.page_type == 'news':
        # Try to fetch news items if model exists
        try:
            News = apps.get_model('announcements', 'News')
            context['news'] = News.objects.filter(is_published=True).order_by('-published_date')
        except LookupError:
            # Model doesn't exist - silently skip
            context['news'] = []
    
    # Render the template specified in the page, or default to default.html
    template = f'pages/{page.template}'
    
    return render(request, template, context)


# Optional: Add decorator for future permission-based pages
def private_page_view(request, slug):
    """
    Optional view for pages that require authentication.
    Can be used for future extension with role-based access.
    """
    # This can be extended in the future for admin-only or role-based pages
    return page_view(request, slug)
