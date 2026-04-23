from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('page/<slug:slug>/', views.page_view, name='page_detail'),
]