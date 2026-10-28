from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('settingsapp', '0031_seed_daarulbayaan_offline_tips'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchoolAboutProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('page_title', models.CharField(blank=True, default='About Us', max_length=120)),
                ('intro', models.TextField(blank=True, default='')),
                ('history', models.TextField(blank=True, default='')),
                ('motto', models.CharField(blank=True, default='', max_length=255)),
                ('vision', models.TextField(blank=True, default='')),
                ('mission', models.TextField(blank=True, default='')),
                ('core_values', models.TextField(blank=True, default='')),
                ('leadership_message', models.TextField(blank=True, default='')),
                ('educational_approach', models.TextField(blank=True, default='')),
                ('cover_image', models.ImageField(blank=True, null=True, upload_to='school/about/')),
                ('featured_image', models.ImageField(blank=True, null=True, upload_to='school/about/')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('school_settings', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='about_profile', to='settingsapp.schoolsettings')),
            ],
            options={
                'ordering': ['page_title'],
            },
        ),
        migrations.CreateModel(
            name='SchoolAboutSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section_type', models.CharField(choices=[('overview', 'Overview'), ('story', 'School Story'), ('value', 'Core Value'), ('leadership', 'Leadership'), ('approach', 'Educational Approach'), ('highlight', 'Highlight'), ('custom', 'Custom')], default='custom', max_length=25)),
                ('title', models.CharField(blank=True, default='', max_length=200)),
                ('content', models.TextField(blank=True, default='')),
                ('image', models.ImageField(blank=True, null=True, upload_to='school/about/sections/')),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('school_about', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='settingsapp.schoolaboutprofile')),
            ],
            options={
                'ordering': ['order', 'created_at'],
            },
        ),
    ]
