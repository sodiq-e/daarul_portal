from django.urls import path
from .views import contact_view, contact_success, contact_message_list

app_name = 'communication'

urlpatterns = [
    path('contact/', contact_view, name='contact'),
    path('contact/success/', contact_success, name='contact_success'),
    path('contact/messages/', contact_message_list, name='contact_message_list'),
]