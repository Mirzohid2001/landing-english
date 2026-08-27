# Migrate bilan tepadagi LIVE announcement + dolzarb taklifni yoqish.

from django.db import migrations

ANNOUNCEMENT = {
    'campaign_id': 'ann_live_sr_aug26',
    'enabled': True,
    'placement': 'announcement',
    'badge': 'live',
    'title': 'Jonli darslar va website ga to‘liq access',
    'description': '',
    'price': 899_000,
    'cta_text': 'Batafsil',
    'cta_link': 'https://t.me/tonacademyuz',
    'order': 0,
    'expires_at': None,
}

CURRENT_OFFER = {
    'campaign_id': 'live_sr_aug26',
    'enabled': True,
    'placement': 'current_offer',
    'badge': 'live',
    'title': 'Jonli darslar',
    'description': 'Jonli darslar + to‘liq website access',
    'offer_label': 'LIVE bundle — 899 000 so‘m',
    'price': 899_000,
    'urgency_text': 'Joylar cheklangan',
    'cta_text': 'Telegram orqali qo‘shilish',
    'cta_link': 'https://t.me/tonacademyuz',
    'order': 0,
    'expires_at': None,
}


def forwards(apps, schema_editor):
    PromoCampaign = apps.get_model('blog', 'PromoCampaign')

    for payload in (ANNOUNCEMENT, CURRENT_OFFER):
        campaign_id = payload['campaign_id']
        defaults = {k: v for k, v in payload.items() if k != 'campaign_id'}
        obj, created = PromoCampaign.objects.get_or_create(
            campaign_id=campaign_id,
            defaults={**defaults, 'campaign_id': campaign_id},
        )
        if not created:
            for key, value in defaults.items():
                setattr(obj, key, value)
            obj.save()


def backwards(apps, schema_editor):
    PromoCampaign = apps.get_model('blog', 'PromoCampaign')
    PromoCampaign.objects.filter(
        campaign_id__in=['ann_live_sr_aug26', 'live_sr_aug26'],
    ).update(enabled=False)


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0019_shorten_jonli_darslar_copy'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
