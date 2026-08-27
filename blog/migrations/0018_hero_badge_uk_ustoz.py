# Generated manually — production migrate da eski hero badge yangilanadi.

from django.db import migrations, models

OLD_BADGE = 'IELTS platform — joylar cheklangan, studentlarga beriladi'
NEW_BADGE = 'UK ustoz + jonli darslar — joylar cheklangan'


def forwards(apps, schema_editor):
    LandingSettings = apps.get_model('blog', 'LandingSettings')
    LandingSettings.objects.filter(hero_badge_text=OLD_BADGE).update(hero_badge_text=NEW_BADGE)
    # Bo‘sh yoki default qolgan yozuvlar ham yangi matnga
    LandingSettings.objects.filter(hero_badge_text='').update(hero_badge_text=NEW_BADGE)


def backwards(apps, schema_editor):
    LandingSettings = apps.get_model('blog', 'LandingSettings')
    LandingSettings.objects.filter(hero_badge_text=NEW_BADGE).update(hero_badge_text=OLD_BADGE)


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0017_landing_ai_card_video'),
    ]

    operations = [
        migrations.AlterField(
            model_name='landingsettings',
            name='hero_badge_text',
            field=models.CharField(
                blank=True,
                default='UK ustoz + jonli darslar — joylar cheklangan',
                max_length=200,
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
