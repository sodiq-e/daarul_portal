from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    # Dynamic page view - catch-all at the end to avoid conflicts
    path('page/<slug:slug>/', views.page_view, name='page_detail'),
]
