# Migrate-only production sync: LandingSettings, FAQ, hero proofs.
# AlterField default lar mavjud DB qatorlarini yangilamaydi — shu migration to‘ldiradi.

from django.db import migrations

SETTINGS = {
    'instagram_url': 'https://www.instagram.com/ton.academy.uz/',
    'youtube_url': 'https://www.youtube.com/@TonAcademyuz',
    'telegram_purchase_url': 'https://t.me/tonacademyuz',
    'base_price_label': 'Platforma + jonli darslar — umrbod access',
    'reassurance_text': 'Bir martalik to‘lov • Jonli darslar • Umrbod access',
    'hero_badge_text': 'UK ustoz + jonli darslar — joylar cheklangan',
}

FAQ_UPDATES = {
    '599 000 so‘mga aynan nimalar kiradi?': (
        'Jonli darslar, 100+ video darslar, AI checker, Reading/Listening/Writing '
        'materiallari, progress tracking va barcha yangilanishlar.'
    ),
    'Jonli darslar bormi?': (
        'Ha, jonli darslar mavjud. Qo‘shimcha LIVE bundle (899k) da Speaking + Reading '
        'LIVE darslar kengaytirilgan formatda beriladi.'
    ),
}


def forwards(apps, schema_editor):
    LandingSettings = apps.get_model('blog', 'LandingSettings')
    FAQ = apps.get_model('blog', 'FAQ')
    LandingHeroProof = apps.get_model('blog', 'LandingHeroProof')
    PromoCampaign = apps.get_model('blog', 'PromoCampaign')

    LandingSettings.objects.all().update(**SETTINGS)

    for question, answer in FAQ_UPDATES.items():
        FAQ.objects.filter(question=question).update(answer=answer)

    # Apostrof/encoding farqi bo‘lsa ham eski UK matnlarni tozalash
    FAQ.objects.filter(
        question__icontains='599',
        answer__icontains='UK ustoz',
    ).update(answer=FAQ_UPDATES['599 000 so‘mga aynan nimalar kiradi?'])
    FAQ.objects.filter(
        question__icontains='Jonli darslar bormi',
        answer__icontains='UK ustoz',
    ).update(answer=FAQ_UPDATES['Jonli darslar bormi?'])

    LandingHeroProof.objects.filter(subtitle__icontains='UK').update(subtitle='jonli format')

    PromoCampaign.objects.filter(
        campaign_id__in=['ann_live_sr_aug26', 'live_sr_aug26'],
    ).update(cta_link=SETTINGS['telegram_purchase_url'], expires_at=None)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0021_fix_social_urls'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
