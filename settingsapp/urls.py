from django.urls import path
from .import views

urlpatterns = [
    path('', views.school_settings, name='school_settings'),
]
