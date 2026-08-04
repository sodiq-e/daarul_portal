from django.db import migrations


def classify_thread_type(thread, participant_count):
    name = (thread.name or '').strip().lower()
    if 'class chat' in name:
        return 'class'
    if participant_count <= 2:
        return 'personal'
    return 'group'


def backfill_thread_types(apps, schema_editor):
    PortalThread = apps.get_model('communication', 'PortalThread')

    for thread in PortalThread.objects.order_by('id'):
        participant_ids = set(thread.participants.values_list('id', flat=True))
        if thread.user_id is not None:
            participant_ids.add(thread.user_id)

        participant_count = len(participant_ids)
        thread.thread_type = classify_thread_type(thread, participant_count)
        thread.save(update_fields=['thread_type'])


class Migration(migrations.Migration):
    dependencies = [
        ('communication', '0006_portalthread_thread_type'),
    ]

    operations = [
        migrations.RunPython(backfill_thread_types, migrations.RunPython.noop),
    ]
