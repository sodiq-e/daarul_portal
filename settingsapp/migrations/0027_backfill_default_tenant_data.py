from urllib.parse import urlsplit

from django.conf import settings
from django.db import migrations


TENANT_SCOPED_MODELS = [
    ('school_classes', 'SchoolClasses'),
    ('school_classes', 'Teacher'),
    ('school_classes', 'ClassTeacher'),
    ('school_classes', 'SchemeOfWork'),
    ('school_classes', 'SchemeWeek'),
    ('students', 'Student'),
    ('students', 'StudentApplication'),
    ('announcements', 'Announcement'),
    ('announcements', 'AnnouncementCategory'),
    ('exams', 'Term'),
    ('exams', 'Subject'),
    ('exams', 'ClassSubject'),
    ('exams', 'ExamType'),
    ('exams', 'Exam'),
    ('exams', 'ExamPaper'),
    ('attendance', 'AttendanceRecord'),
    ('attendance', 'AttendanceSession'),
    ('attendance', 'AttendanceHoliday'),
    ('results', 'GradeScale'),
    ('results', 'ResultTemplate'),
    ('results', 'StudentResult'),
    ('results', 'TermResult'),
    ('results', 'Promotion'),
    ('results', 'ReportCardComment'),
    ('results', 'StudentConduct'),
    ('payroll', 'Staff'),
    ('payroll', 'SalaryComponent'),
    ('payroll', 'Payslip'),
    ('payroll', 'PayrollDashboard'),
    ('payroll', 'SchoolExpense'),
    ('payroll', 'SchoolFee'),
    ('payroll', 'StudentInvoice'),
    ('payroll', 'StudentPayment'),
    ('communication', 'Message'),
    ('communication', 'PortalThread'),
    ('cbt', 'QuestionBank'),
    ('cbt', 'CBTExam'),
    ('cbt', 'CBTQuestion'),
    ('cbt', 'CBTStudentAttempt'),
    ('psychomotor', 'TraitCategory'),
    ('psychomotor', 'Trait'),
    ('psychomotor', 'StudentTraitRating'),
    ('staff_attendance', 'StudentAttendanceSettings'),
    ('staff_attendance', 'AttendanceSettings'),
    ('staff_attendance', 'StaffAttendance'),
]


def normalize_hostname(hostname, base_domain):
    hostname = (hostname or '').strip().lower().rstrip('.')
    if '://' in hostname:
        hostname = urlsplit(hostname).hostname or ''
    else:
        hostname = urlsplit(f'//{hostname}').hostname or ''
    return hostname or f'daarulbayaan.{base_domain}'


def backfill_default_tenant(apps, schema_editor):
    Tenant = apps.get_model('settingsapp', 'Tenant')
    SchoolSettings = apps.get_model('settingsapp', 'SchoolSettings')
    Membership = apps.get_model('settingsapp', 'TenantMembership')
    User = apps.get_model('auth', 'User')

    base_domain = str(getattr(settings, 'TENANT_BASE_DOMAIN', 'localhost')).strip().lower().strip('.')
    tenant, created = Tenant.objects.get_or_create(
        slug='daarulbayaan',
        defaults={
            'name': 'Daarul Bayaan Islamic School',
            'hostname': f'daarulbayaan.{base_domain}',
            'is_active': True,
        },
    )
    desired_hostname = normalize_hostname(tenant.hostname, base_domain)
    if created or tenant.hostname != desired_hostname:
        tenant.hostname = desired_hostname
        tenant.is_active = True
        tenant.save(update_fields=['hostname', 'is_active'])

    settings_obj = SchoolSettings.objects.filter(tenant=tenant).first()
    if settings_obj is None:
        settings_obj = SchoolSettings.objects.order_by('id').first()
        if settings_obj is not None and SchoolSettings.objects.filter(tenant__isnull=False).exclude(pk=settings_obj.pk).exists():
            settings_obj = None
        if settings_obj is not None:
            settings_obj.tenant = tenant
            settings_obj.save(update_fields=['tenant'])
        else:
            SchoolSettings.objects.create(tenant=tenant)

    for app_label, model_name in TENANT_SCOPED_MODELS:
        model = apps.get_model(app_label, model_name)
        if model is not None and any(field.name == 'tenant' for field in model._meta.get_fields()):
            model.objects.filter(tenant__isnull=True).update(tenant=tenant)

    for user in User.objects.filter(is_superuser=False):
        roles = set()
        if apps.get_model('school_classes', 'Teacher').objects.filter(user=user).exists():
            roles.add('teacher')
        if apps.get_model('payroll', 'Staff').objects.filter(user=user).exists():
            roles.add('staff')
        if apps.get_model('students', 'Student').objects.filter(user=user).exists():
            roles.add('student')

        for group in user.groups.filter(name__in=['Teacher', 'Staff', 'Student', 'Parent']):
            roles.add(group.name.lower())

        for role in roles:
            Membership.objects.get_or_create(
                user=user,
                tenant=tenant,
                role=role,
                defaults={'is_active': True},
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('settingsapp', '0026_tenantmembership'),
        ('school_classes', '0007_teacher_tenant'),
        ('students', '0012_studentapplication_tenant_alter_student_tenant'),
        ('announcements', '0005_announcementcategory_tenant_and_more'),
        ('exams', '0013_alter_classsubject_unique_together_and_more'),
        ('attendance', '0009_attendanceholiday_tenant_and_more'),
        ('results', '0015_alter_resulttemplate_unique_together_and_more'),
        ('payroll', '0007_staff_user'),
        ('communication', '0008_message_tenant_portalthread_tenant'),
        ('cbt', '0008_cbtanswer_tenant_cbtexam_tenant_cbtquestion_tenant_and_more'),
        ('psychomotor', '0002_studenttraitrating_tenant_trait_tenant_and_more'),
        ('staff_attendance', '0004_attendancesettings_tenant_staffattendance_tenant_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(backfill_default_tenant, noop_reverse),
    ]
