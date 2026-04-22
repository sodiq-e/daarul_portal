from django.urls import path
from . import views

urlpatterns = [
    # School Classes
    path('', views.ClassListView.as_view(), name='class_list'),
    path('add/', views.add_class, name='add_class'),

    # Teacher Profile
    path('teachers/apply/', views.TeacherApplicationView.as_view(), name='teacher_apply'),
    path('teachers/profile/', views.TeacherProfileView.as_view(), name='teacher_profile'),
    path('teachers/profile/edit/', views.TeacherProfileEditView.as_view(), name='teacher_profile_edit'),

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
    path('teachers/schemes/', views.TeacherSchemeListView.as_view(), name='teacher_scheme_list'),
    path('teachers/schemes/add/', views.TeacherSchemeCreateView.as_view(), name='teacher_scheme_add'),
    path('teachers/schemes/<int:pk>/', views.TeacherSchemeDetailView.as_view(), name='teacher_scheme_detail'),
    path('teachers/schemes/<int:pk>/edit/', views.TeacherSchemeUpdateView.as_view(), name='teacher_scheme_edit'),
    path('teachers/schemes/<int:scheme_id>/week/add/', views.SchemeWeekCreateView.as_view(), name='scheme_week_add'),
    path('teachers/schemes/week/<int:pk>/edit/', views.SchemeWeekUpdateView.as_view(), name='scheme_week_edit'),
    path('teachers/schemes/week/<int:week_id>/complete/', views.mark_week_complete, name='mark_week_complete'),
    path('teachers/schemes/week/<int:week_id>/incomplete/', views.mark_week_incomplete, name='mark_week_incomplete'),
    path('teachers/schemes/<int:scheme_id>/submit/', views.submit_scheme_for_approval, name='submit_scheme'),

    # Admin: Scheme Approval
    path('admin/schemes/', views.AdminSchemeListView.as_view(), name='admin_scheme_list'),
    path('admin/schemes/<int:pk>/', views.AdminSchemeDetailView.as_view(), name='admin_scheme_detail'),
    path('admin/schemes/<int:scheme_id>/approve/', views.approve_scheme, name='approve_scheme'),
    path('admin/schemes/<int:scheme_id>/reject/', views.reject_scheme, name='reject_scheme'),
]
