# Productiondagi eski Instagram/YouTube URL larni yangilash.
# 0016 faqat field default ni o‘zgartirgan — mavjud LandingSettings qatori yangilanmagan.
# Label templateda hardcode (@ton.academy.uz), href esa DB dan — shuning uchun
# lokal to‘g‘ri, serverda boshqa ssilka ochilgan.

from django.db import migrations

CORRECT_IG = 'https://www.instagram.com/ton.academy.uz/'
CORRECT_YT = 'https://www.youtube.com/@TonAcademyuz'
CORRECT_TG = 'https://t.me/tonacademyuz'


def forwards(apps, schema_editor):
    LandingSettings = apps.get_model('blog', 'LandingSettings')
    PromoCampaign = apps.get_model('blog', 'PromoCampaign')

    LandingSettings.objects.all().update(
        instagram_url=CORRECT_IG,
        youtube_url=CORRECT_YT,
        telegram_purchase_url=CORRECT_TG,
    )
    PromoCampaign.objects.all().update(cta_link=CORRECT_TG)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0020_enable_live_announcement'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
