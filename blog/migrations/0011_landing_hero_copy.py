from django.db import migrations, models


HERO_COPY = {
    'hero_headline': 'Kafolatlangan /\nIELTS - 7.0 + Online program',
    'hero_subtitle': (
        'IELTS balingizni Britaniyalik ustozlar va kafolatlangan tizim orqali o‘rganing'
    ),
    'primary_cta_text': 'Bepul daraja testini boshlash',
    'secondary_cta_text': 'Telegram orqali xarid qilish',
}


def apply_hero_copy(apps, schema_editor):
    LandingSettings = apps.get_model('blog', 'LandingSettings')
    LandingSettings.objects.update_or_create(pk=1, defaults=HERO_COPY)


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0010_landing_v11'),
    ]

    operations = [
        migrations.AlterField(
            model_name='landingsettings',
            name='hero_headline',
            field=models.CharField(
                default='Kafolatlangan /\nIELTS - 7.0 + Online program',
                max_length=300,
            ),
        ),
        migrations.AlterField(
            model_name='landingsettings',
            name='hero_subtitle',
            field=models.TextField(
                default=(
                    'IELTS balingizni Britaniyalik ustozlar va kafolatlangan tizim '
                    'orqali o‘rganing'
                ),
            ),
        ),
        migrations.AlterField(
            model_name='landingsettings',
            name='primary_cta_text',
            field=models.CharField(default='Bepul daraja testini boshlash', max_length=120),
        ),
        migrations.AlterField(
            model_name='landingsettings',
            name='secondary_cta_text',
            field=models.CharField(default='Telegram orqali xarid qilish', max_length=120),
        ),
        migrations.RunPython(apply_hero_copy, migrations.RunPython.noop),
    ]
