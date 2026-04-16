from django.urls import path
from . import views

urlpatterns = [
    path('', views.ClassListView.as_view(), name='class_list'),
    path('add/', views.add_class, name='add_class'),
]
