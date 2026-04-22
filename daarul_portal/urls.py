from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import CustomLoginView


def home(request):
    return render(request, 'home.html')


urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', CustomLoginView.as_view(), name='login'),

    path('', home, name='home'),

    path('', include('communication.urls')),
    path('accounts/', include('accounts.urls')),
    path('results/', include('results.urls')),
    path('settings/', include('settingsapp.urls')),
    path('classes/', include('school_classes.urls')),
    path('students/', include('students.urls')),
    path('exams/', include('exams.urls')),
    path('attendance/', include('attendance.urls')),
    path('announcements/', include('announcements.urls')),
    path('payroll/', include('payroll.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
