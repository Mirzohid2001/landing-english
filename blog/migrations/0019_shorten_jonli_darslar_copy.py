# Production migrate: LIVE offer + benefit card matnlarini qisqartirish.

from django.db import migrations

OFFER_UPDATES = {
    'live_sr_aug26': {
        'title': 'Jonli darslar',
        'description': 'Jonli darslar + to‘liq website access',
    },
    'ann_live_sr_aug26': {
        'title': 'Jonli darslar va website ga to‘liq access',
        'description': '',
    },
}

OLD_BENEFIT_TEXT = 'UK ustoz va yana 2 ta professional ustozlardan jonli darslar.'
NEW_BENEFIT_TEXT = 'Jonli darslar.'


def forwards(apps, schema_editor):
    PromoCampaign = apps.get_model('blog', 'PromoCampaign')
    LandingBenefitCard = apps.get_model('blog', 'LandingBenefitCard')

    for campaign_id, fields in OFFER_UPDATES.items():
        PromoCampaign.objects.filter(campaign_id=campaign_id).update(**fields)

    # Eski matn bilan saqlangan barcha offer/announcement yozuvlari
    PromoCampaign.objects.filter(
        title='UK ustoz + 2 professional ustozdan jonli darslar',
    ).update(title='Jonli darslar')
    PromoCampaign.objects.filter(
        description='UK ustoz va yana 2 ta professional ustozlardan jonli darslar + to‘liq website access',
    ).update(description='Jonli darslar + to‘liq website access')
    PromoCampaign.objects.filter(
        title='UK ustoz va yana 2 ta professional ustozlardan jonli darslar va website ga toliq access',
    ).update(title='Jonli darslar va website ga to‘liq access')

    LandingBenefitCard.objects.filter(text=OLD_BENEFIT_TEXT).update(text=NEW_BENEFIT_TEXT)
    LandingBenefitCard.objects.filter(title='Jonli darslar', text__icontains='UK ustoz').update(
        text=NEW_BENEFIT_TEXT,
    )


def backwards(apps, schema_editor):
    PromoCampaign = apps.get_model('blog', 'PromoCampaign')
    LandingBenefitCard = apps.get_model('blog', 'LandingBenefitCard')

    PromoCampaign.objects.filter(campaign_id='live_sr_aug26').update(
        title='UK ustoz + 2 professional ustozdan jonli darslar',
        description='UK ustoz va yana 2 ta professional ustozlardan jonli darslar + to‘liq website access',
    )
    PromoCampaign.objects.filter(campaign_id='ann_live_sr_aug26').update(
        title='UK ustoz va yana 2 ta professional ustozlardan jonli darslar va website ga toliq access',
    )
    LandingBenefitCard.objects.filter(text=NEW_BENEFIT_TEXT, title='Jonli darslar').update(
        text=OLD_BENEFIT_TEXT,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0018_hero_badge_uk_ustoz'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
