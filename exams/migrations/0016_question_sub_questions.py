from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0015_exam_scoring_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='sub_questions',
            field=models.JSONField(blank=True, default=list, help_text='Nested sub-questions for numbered theory questions'),
        ),
    ]
