from django.db import migrations


DEFAULT_TIPS = [
    'Try active recall: close your notes and explain one idea from memory.',
    'Short, focused study sessions with brief breaks can help you stay attentive.',
    'Review important ideas again after a day, then a few days later.',
    'Practice with questions instead of only rereading your notes.',
    'Explain a difficult topic in your own words to spot gaps in understanding.',
    'Write down questions as they come up, then ask your teacher.',
    'A clear, quiet study space can make it easier to concentrate.',
    'Sleep and rest support learning and memory.',
    'Keep your login details private and sign out on shared devices.',
    'Offline? Changes were not submitted. Reconnect, then try again.',
]


def seed_daarulbayaan_tips(apps, schema_editor):
    Tenant = apps.get_model('settingsapp', 'Tenant')
    DidYouKnowTip = apps.get_model('settingsapp', 'DidYouKnowTip')
    tenant = Tenant.objects.filter(slug='daarulbayaan').first()
    if tenant is None:
        return

    for order, message in enumerate(DEFAULT_TIPS, start=1):
        DidYouKnowTip.objects.get_or_create(
            tenant_id=tenant.pk,
            message=message,
            defaults={'order': order, 'is_active': True},
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('settingsapp', '0030_didyouknowtip'),
    ]

    operations = [
        migrations.RunPython(seed_daarulbayaan_tips, noop_reverse),
    ]
