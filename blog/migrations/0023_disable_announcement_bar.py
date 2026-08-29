# Tepadagi LIVE announcement barni o‘chirish.

from django.db import migrations


def forwards(apps, schema_editor):
    PromoCampaign = apps.get_model('blog', 'PromoCampaign')
    PromoCampaign.objects.filter(
        placement='announcement',
    ).update(enabled=False)
    PromoCampaign.objects.filter(
        campaign_id='ann_live_sr_aug26',
    ).update(enabled=False)


def backwards(apps, schema_editor):
    PromoCampaign = apps.get_model('blog', 'PromoCampaign')
    PromoCampaign.objects.filter(
        campaign_id='ann_live_sr_aug26',
    ).update(enabled=True)


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0022_sync_landing_copy_and_urls'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
