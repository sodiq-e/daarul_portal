from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import CustomLoginView
from pages.models import Page
from school_classes.urls import class_urlpatterns, teacher_urlpatterns


def home(request):
    pages = Page.objects.filter(
        is_published=True,
        show_on_homepage=True
    )
    print("PAGES:", pages)

    return render(request, 'home.html', {
        'pages': pages
    })


urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', CustomLoginView.as_view(), name='login'),

    path('', home, name='home'),

    path('', include('communication.urls')),
    path('accounts/', include('accounts.urls')),
    path('results/', include('results.urls')),
    path('settings/', include('settingsapp.urls')),
    path('classes/', include((class_urlpatterns, 'school_classes'))),
    path('students/', include('students.urls')),
    path('exams/', include('exams.urls')),
    path('attendance/', include('attendance.urls')),
    path('announcements/', include('announcements.urls')),
    path('payroll/', include('payroll.urls')),
    path('', include('pages.urls')),
    path('teachers/', include((teacher_urlpatterns, 'teachers'))),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
