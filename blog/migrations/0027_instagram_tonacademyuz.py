# Instagram: ton.academy.uz → tonacademyuz

from django.db import migrations, models

NEW_IG = 'https://www.instagram.com/tonacademyuz/'


def forwards(apps, schema_editor):
    LandingSettings = apps.get_model('blog', 'LandingSettings')
    LandingSettings.objects.all().update(instagram_url=NEW_IG)


def backwards(apps, schema_editor):
    LandingSettings = apps.get_model('blog', 'LandingSettings')
    LandingSettings.objects.all().update(
        instagram_url='https://www.instagram.com/ton.academy.uz/',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0026_enable_posthog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='landingsettings',
            name='instagram_url',
            field=models.URLField(
                blank=True,
                default='https://www.instagram.com/tonacademyuz/',
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
