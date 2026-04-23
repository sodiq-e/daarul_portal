from django.urls import path
from . import views

urlpatterns = [
    path('page/<slug:slug>/', views.page_view),
    path('<str:prefix>/page/<slug:slug>/', views.page_view),
]
