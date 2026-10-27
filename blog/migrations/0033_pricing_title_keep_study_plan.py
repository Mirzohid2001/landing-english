# Pricing title: UK ustozlar + Study plan (ikkala qator)

from django.db import migrations, models

NEW_TITLE = 'UK ustozlar bilan jonli darslar\nStudy plan'


def forwards(apps, schema_editor):
    LandingSettings = apps.get_model('blog', 'LandingSettings')
    LandingSettings.objects.all().update(pricing_card_title=NEW_TITLE)


def backwards(apps, schema_editor):
    LandingSettings = apps.get_model('blog', 'LandingSettings')
    LandingSettings.objects.filter(pricing_card_title=NEW_TITLE).update(
        pricing_card_title='UK ustozlar bilan jonli darslar',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0032_pricing_card_uk_ustozlar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='landingsettings',
            name='pricing_card_title',
            field=models.CharField(
                default='UK ustozlar bilan jonli darslar\nStudy plan',
                max_length=120,
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
