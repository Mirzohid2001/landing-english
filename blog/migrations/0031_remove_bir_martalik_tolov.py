# «Bir martalik to‘lov» matnini reassurance dan olib tashlash.

from django.db import migrations, models

NEW_REASSURANCE = 'Jonli darslar • Study plan'


def forwards(apps, schema_editor):
    LandingSettings = apps.get_model('blog', 'LandingSettings')
    LandingSettings.objects.all().update(reassurance_text=NEW_REASSURANCE)
    # Eski variantlar
    LandingSettings.objects.filter(
        reassurance_text__icontains='Bir martalik',
    ).update(reassurance_text=NEW_REASSURANCE)


def backwards(apps, schema_editor):
    LandingSettings = apps.get_model('blog', 'LandingSettings')
    LandingSettings.objects.filter(reassurance_text=NEW_REASSURANCE).update(
        reassurance_text='Bir martalik to‘lov • Jonli darslar • Study plan',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0030_umrbod_to_study_plan'),
    ]

    operations = [
        migrations.AlterField(
            model_name='landingsettings',
            name='reassurance_text',
            field=models.CharField(
                default='Jonli darslar • Study plan',
                max_length=200,
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
