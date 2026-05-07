from django.urls import path
from .views import (
    contact_view,
    contact_success,
    AdminMessageListView,
    AdminMessageDetailView,
    AdminPortalUserListView,
    AdminPortalThreadView,
    PortalInboxView,
    PortalThreadDetailView,
)

urlpatterns = [
    path('contact/', contact_view, name='contact'),
    path('contact/success/', contact_success, name='contact_success'),

    path('admin/messages/', AdminMessageListView.as_view(), name='admin_messages_list'),
    path('admin/messages/<int:pk>/', AdminMessageDetailView.as_view(), name='admin_message_detail'),
    path('admin/messages/portal/', AdminPortalUserListView.as_view(), name='admin_portal_users_list'),
    path('admin/messages/portal/<int:user_id>/', AdminPortalThreadView.as_view(), name='admin_portal_thread_detail'),

    path('portal/messages/', PortalInboxView.as_view(), name='portal_messages_list'),
    path('portal/messages/thread/', PortalThreadDetailView.as_view(), name='portal_thread_detail'),
]
