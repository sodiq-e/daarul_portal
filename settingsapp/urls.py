from django.urls import path
from . import views

urlpatterns = [
    path('', views.school_settings, name='school_settings'),
    path('did-you-know/', views.did_you_know_tips, name='did_you_know_tips'),
    path('tenants/', views.tenant_dashboard, name='tenant_dashboard'),
    path('tenants/new/', views.tenant_form, name='tenant_create'),
    path('tenants/<int:tenant_id>/edit/', views.tenant_form, name='tenant_edit'),
    path('tenants/<int:tenant_id>/memberships/', views.tenant_memberships, name='tenant_memberships'),
    path('tenants/<int:tenant_id>/portal-settings/', views.tenant_portal_settings, name='tenant_portal_settings'),
]
