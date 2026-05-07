from django.urls import path
from .views import contact_view, contact_success, AdminMessageListView, AdminMessageDetailView

urlpatterns = [
    path('contact/', contact_view, name='contact'),
    path('contact/success/', contact_success, name='contact_success'),
    
    # Admin message management
    path('admin/messages/', AdminMessageListView.as_view(), name='admin_messages_list'),
    path('admin/messages/<int:pk>/', AdminMessageDetailView.as_view(), name='admin_message_detail'),
]