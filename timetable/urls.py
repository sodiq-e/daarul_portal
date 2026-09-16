from django.urls import path

from . import views

app_name = 'timetable'

urlpatterns = [
    path('', views.timetable_list, name='list'),
    path('create/', views.timetable_create, name='create'),
    path('<int:pk>/', views.timetable_detail, name='detail'),
    path('<int:pk>/copy/', views.timetable_copy, name='copy'),
    path('<int:pk>/fill/', views.timetable_fill, name='fill'),
    path('<int:pk>/publish/', views.timetable_publish, name='publish'),
    path('<int:pk>/slots/add/', views.timetable_add_slot, name='add_slot'),
    path('<int:pk>/slots/<int:slot_id>/edit/', views.timetable_edit_slot, name='edit_slot'),
    path('<int:pk>/slots/<int:slot_id>/delete/', views.timetable_delete_slot, name='delete_slot'),
    path('<int:pk>/days/add/', views.timetable_add_day, name='add_day'),
    path('<int:pk>/days/<int:day_id>/delete/', views.timetable_remove_day, name='delete_day'),
]
