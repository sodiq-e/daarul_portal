import re

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.apps import apps
from django.urls import NoReverseMatch, URLPattern, URLResolver, get_resolver, reverse

from .models import Page


GLOBAL_SEARCH_DEFAULTS = [
    {
        'title': 'Home',
        'description': 'Return to the main portal dashboard and landing page.',
        'url': '/',
        'keywords': ['home', 'dashboard', 'welcome', 'portal'],
    },
    {
        'title': 'Students',
        'description': 'Manage student records, profiles, applications, and admissions.',
        'url': '/students/',
        'keywords': ['students', 'student', 'admissions', 'profile'],
    },
    {
        'title': 'Results',
        'description': 'Open the results overview and report card dashboard.',
        'url': '/results/',
        'keywords': ['results', 'report cards', 'broadsheet', 'performance', 'exam', 'exams', 'grades'],
    },
    {
        'title': 'Classes',
        'description': 'Browse class lists, teacher assignments, and timetable sections.',
        'url': '/classes/',
        'keywords': ['classes', 'class', 'timetable', 'teachers'],
    },
    {
        'title': 'Announcements',
        'description': 'Read updates, notices, and important school announcements.',
        'url': '/announcements/',
        'keywords': ['announcements', 'news', 'updates', 'notice'],
    },
    {
        'title': 'Fees & Invoices',
        'description': 'Review school fees, invoices, and payment records.',
        'url': '/payroll/invoices/',
        'keywords': ['fees', 'invoice', 'payments', 'payroll'],
    },
]


NON_NAVIGATION_ROUTE_PARTS = {
    'action', 'api', 'approve', 'delete', 'export', 'import', 'incomplete',
    'logout', 'reject', 'save', 'submit', 'upload',
}


def _named_route_results(patterns=None, namespaces=()):
    """Build search entries from named, static GET routes in the URL configuration."""
    if patterns is None:
        patterns = get_resolver().url_patterns

    results = []
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            nested_namespaces = namespaces + ((pattern.namespace,) if pattern.namespace else ())
            results.extend(_named_route_results(pattern.url_patterns, nested_namespaces))
            continue

        if not isinstance(pattern, URLPattern) or not pattern.name or pattern.pattern.converters:
            continue

        route_path = str(pattern.pattern).strip('/')
        route_parts = set(route_path.lower().replace('-', '_').split('/'))
        name_parts = set(pattern.name.lower().split('_'))
        if route_parts & NON_NAVIGATION_ROUTE_PARTS or name_parts & NON_NAVIGATION_ROUTE_PARTS:
            continue

        route_name = ':'.join(namespaces + (pattern.name,))
        try:
            url = reverse(route_name)
        except NoReverseMatch:
            continue

        title = pattern.name.replace('_', ' ').title()
        view = pattern.callback
        view_class = getattr(view, 'view_class', None)
        view_name = getattr(view_class or view, '__name__', '')
        view_description = getattr(view_class or view, '__doc__', '') or ''
        route_terms = ' '.join((route_name, route_path, view_name, view_description)).strip()
        results.append({
            'title': title,
            'description': f"Portal function at /{route_path}/" if route_path else 'Portal home page',
            'url': url,
            'keywords': [route_terms],
        })

    return results


def _search_ranked_matches(items, query):
    query_tokens = [token for token in re.split(r'\s+', query.lower().strip()) if token]
    if not query_tokens:
        return items

    ranked = []
    for item in items:
        haystack = ' '.join([
            item.get('title', ''),
            item.get('description', ''),
            ' '.join(item.get('keywords', []) or []),
            item.get('url', ''),
        ]).lower()

        if not haystack:
            continue

        matches = sum(1 for token in query_tokens if token in haystack)
        if matches == 0:
            continue

        rank = 0
        if item.get('title', '').lower().startswith(query.lower()):
            rank += 100
        if query.lower() in item.get('title', '').lower():
            rank += 50
        if query.lower() in haystack:
            rank += 20
        rank += matches
        ranked.append((rank, item))

    ranked.sort(key=lambda entry: entry[0], reverse=True)
    return [item for _, item in ranked]


def global_search(request):
    query = (request.GET.get('q') or '').strip()
    results = list(GLOBAL_SEARCH_DEFAULTS)

    if not query:
        return JsonResponse({'query': query, 'results': results[:10]})

    model_results = []

    try:
        from announcements.models import Announcement
        for announcement in Announcement.objects.filter(is_active=True).order_by('-created_at')[:10]:
            model_results.append({
                'title': announcement.title,
                'description': announcement.excerpt or (announcement.content[:120] if announcement.content else 'Announcement'),
                'url': reverse('announcement_list'),
                'keywords': [announcement.title, 'announcement', 'news', 'updates'],
            })
    except Exception:
        pass

    try:
        from students.models import Student
        for student in Student.objects.select_related('student_class').order_by('surname', 'other_names')[:10]:
            display_name = student.full_name() or str(student)
            model_results.append({
                'title': display_name,
                'description': f"Admission {student.admission_no}" + (f" • {student.student_class.class_name}" if getattr(student.student_class, 'class_name', None) else ''),
                'url': f"/students/{student.pk}/",
                'keywords': [display_name, student.admission_no, 'student', 'profile'],
            })
    except Exception:
        pass

    try:
        from school_classes.models import Teacher, SchoolClasses
        for teacher in Teacher.objects.select_related('user').all()[:10]:
            name = str(teacher)
            model_results.append({
                'title': name,
                'description': 'Teacher profile and staff details',
                'url': reverse('teachers:teacher_list'),
                'keywords': [name, 'teacher', 'staff'],
            })

        for school_class in SchoolClasses.objects.all()[:10]:
            model_results.append({
                'title': school_class.class_name,
                'description': school_class.description or 'Class details',
                'url': reverse('school_classes:class_list'),
                'keywords': [school_class.class_name, 'class', 'students', 'teacher'],
            })
    except Exception:
        pass

    for page in Page.objects.filter(is_published=True).order_by('-updated_at')[:15]:
        model_results.append({
            'title': page.title,
            'description': (page.content or '')[:140],
            'url': f"/page/{page.slug}/",
            'keywords': [page.title, page.slug, 'page', (page.content or '')[:200]],
        })

    combined = results + _named_route_results() + model_results
    filtered = _search_ranked_matches(combined, query)

    unique = []
    seen_urls = set()
    for item in filtered[:50]:
        url = item.get('url') or ''
        if url and url in seen_urls:
            continue
        seen_urls.add(url)
        unique.append(item)

    return JsonResponse({'query': query, 'results': unique})


def page_view(request, slug, prefix=None):
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
