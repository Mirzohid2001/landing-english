# Productionda PostHog token bo‘sh qolgan — snippet chiqmagan.
# Migrate bilan token + host ni majburiy yozish.

from django.db import migrations

POSTHOG_KEY = 'phc_CBNfRo5dzYZE7zJK8VT5VwkvwyGdB8NJBEtjSP9YYYFT'
POSTHOG_HOST = 'https://us.i.posthog.com'


def forwards(apps, schema_editor):
    LandingSettings = apps.get_model('blog', 'LandingSettings')
    LandingSettings.objects.all().update(
        posthog_project_api_key=POSTHOG_KEY,
        posthog_api_host=POSTHOG_HOST,
    )


def backwards(apps, schema_editor):
    LandingSettings = apps.get_model('blog', 'LandingSettings')
    LandingSettings.objects.all().update(posthog_project_api_key='')


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0025_disable_current_offer'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
