from django.urls import path
from . import views

# School Classes URLs
class_urlpatterns = [
    path('', views.ClassListView.as_view(), name='class_list'),
    path('add/', views.add_class, name='add_class'),
    path('<int:pk>/', views.ClassDetailView.as_view(), name='class_detail'),
]

# Teacher URLs
teacher_urlpatterns = [
    # Teacher Dashboard
    path('', views.teacher_dashboard, name='teacher_dashboard'),
    
    # Teacher Profile
    path('apply/', views.TeacherApplicationView.as_view(), name='teacher_apply'),
    path('profile/', views.TeacherProfileView.as_view(), name='teacher_profile'),
    path('profile/edit/', views.TeacherProfileEditView.as_view(), name='teacher_profile_edit'),

    # Admin: Teacher Management
    path('admin/teachers/', views.TeacherListView.as_view(), name='teacher_list'),
    path('admin/teachers/<int:pk>/', views.TeacherDetailView.as_view(), name='teacher_detail'),
    path('admin/teachers/<int:pk>/approve/', views.approve_teacher, name='approve_teacher'),
    path('admin/teachers/<int:pk>/reject/', views.reject_teacher, name='reject_teacher'),

    # Admin: Class-Teacher Assignment
    path('admin/class-teachers/', views.ClassTeacherListView.as_view(), name='class_teacher_list'),
    path('admin/class-teachers/add/', views.ClassTeacherCreateView.as_view(), name='class_teacher_add'),
    path('admin/class-teachers/<int:pk>/edit/', views.ClassTeacherUpdateView.as_view(), name='class_teacher_edit'),
    path('admin/class-teachers/<int:pk>/deactivate/', views.deactivate_class_teacher, name='deactivate_class_teacher'),

    # Admin: Teacher Permissions
    path('admin/permissions/', views.TeacherPermissionsView.as_view(), name='teacher_permissions'),
    path('admin/permissions/<int:teacher_id>/', views.TeacherPermissionsView.as_view(), name='teacher_permissions_detail'),
    path('admin/permissions/<int:teacher_id>/grant/<str:permission_code>/', views.grant_teacher_permission, name='grant_permission'),
    path('admin/permissions/<int:teacher_id>/revoke/<str:permission_code>/', views.revoke_teacher_permission, name='revoke_permission'),
    path('admin/permissions/bulk/', views.BulkPermissionView.as_view(), name='bulk_permissions'),

    # Teacher: Scheme of Work
    path('schemes/', views.TeacherSchemeListView.as_view(), name='teacher_scheme_list'),
    path('schemes/add/', views.TeacherSchemeCreateView.as_view(), name='teacher_scheme_add'),
    path('schemes/<int:pk>/', views.TeacherSchemeDetailView.as_view(), name='teacher_scheme_detail'),
    path('schemes/<int:pk>/edit/', views.TeacherSchemeUpdateView.as_view(), name='teacher_scheme_edit'),
    path('schemes/<int:scheme_id>/week/add/', views.SchemeWeekCreateView.as_view(), name='scheme_week_add'),
    path('schemes/week/<int:pk>/edit/', views.SchemeWeekUpdateView.as_view(), name='scheme_week_edit'),
    path('schemes/week/<int:week_id>/complete/', views.mark_week_complete, name='mark_week_complete'),
    path('schemes/week/<int:week_id>/incomplete/', views.mark_week_incomplete, name='mark_week_incomplete'),
    path('schemes/<int:scheme_id>/submit/', views.submit_scheme_for_approval, name='submit_scheme'),

    # Admin: Scheme Approval
    path('admin/schemes/', views.AdminSchemeListView.as_view(), name='admin_scheme_list'),
    path('admin/schemes/<int:pk>/', views.AdminSchemeDetailView.as_view(), name='admin_scheme_detail'),
    path('admin/schemes/<int:scheme_id>/approve/', views.approve_scheme, name='approve_scheme'),
    path('admin/schemes/<int:scheme_id>/reject/', views.reject_scheme, name='reject_scheme'),
]

urlpatterns = class_urlpatterns + teacher_urlpatterns
