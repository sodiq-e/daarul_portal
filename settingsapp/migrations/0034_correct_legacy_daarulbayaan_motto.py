from django.db import migrations


LEGACY_MOTTO = 'Knowledge for the Fear of God'
APPROVED_MOTTO = 'Knowledge for the Fear of Allah'


def correct_legacy_daarulbayaan_motto(apps, schema_editor):
    Tenant = apps.get_model('settingsapp', 'Tenant')
    SchoolSettings = apps.get_model('settingsapp', 'SchoolSettings')
    SchoolAboutProfile = apps.get_model('settingsapp', 'SchoolAboutProfile')

    tenant = Tenant.objects.filter(slug='daarulbayaan').first()
    if tenant is None:
        return

    school_settings = SchoolSettings.objects.filter(tenant_id=tenant.pk).first()
    if school_settings is None:
        return

    profile = SchoolAboutProfile.objects.filter(
        school_settings_id=school_settings.pk,
        motto=LEGACY_MOTTO,
    ).first()
    if profile is not None:
        profile.motto = APPROVED_MOTTO
        profile.save(update_fields=['motto', 'updated_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('settingsapp', '0033_seed_daarulbayaan_about_profile'),
    ]

    operations = [
        migrations.RunPython(correct_legacy_daarulbayaan_motto, migrations.RunPython.noop),
    ]
