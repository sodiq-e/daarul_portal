from django.urls import path
from . import views

urlpatterns = [
    path('', views.AnnouncementListView.as_view(), name='announcement_list'),
    path('<int:pk>/', views.AnnouncementDetailView.as_view(), name='announcement_detail'),
    path('create/', views.AnnouncementCreateView.as_view(), name='announcement_create'),
    path('<int:pk>/edit/', views.AnnouncementUpdateView.as_view(), name='announcement_edit'),
    path('<int:pk>/delete/', views.AnnouncementDeleteView.as_view(), name='announcement_delete'),
]