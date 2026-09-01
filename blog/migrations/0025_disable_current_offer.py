# 899k dolzarb taklif kartasini o‘chirish.

from django.db import migrations


def forwards(apps, schema_editor):
    PromoCampaign = apps.get_model('blog', 'PromoCampaign')
    PromoCampaign.objects.filter(
        placement='current_offer',
    ).update(enabled=False)
    PromoCampaign.objects.filter(
        campaign_id='live_sr_aug26',
    ).update(enabled=False)


def backwards(apps, schema_editor):
    PromoCampaign = apps.get_model('blog', 'PromoCampaign')
    PromoCampaign.objects.filter(
        campaign_id='live_sr_aug26',
    ).update(enabled=True)


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0024_landing_platform_url'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
