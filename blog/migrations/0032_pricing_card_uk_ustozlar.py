# Pricing kartasi title: Study plan → UK ustozlar bilan jonli darslar

from django.db import migrations, models

NEW_TITLE = 'UK ustozlar bilan jonli darslar'


def forwards(apps, schema_editor):
    LandingSettings = apps.get_model('blog', 'LandingSettings')
    LandingSettings.objects.all().update(pricing_card_title=NEW_TITLE)


def backwards(apps, schema_editor):
    LandingSettings = apps.get_model('blog', 'LandingSettings')
    LandingSettings.objects.filter(pricing_card_title=NEW_TITLE).update(
        pricing_card_title='Study plan',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0031_remove_bir_martalik_tolov'),
    ]

    operations = [
        migrations.AlterField(
            model_name='landingsettings',
            name='pricing_card_title',
            field=models.CharField(
                default='UK ustozlar bilan jonli darslar',
                max_length=120,
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
