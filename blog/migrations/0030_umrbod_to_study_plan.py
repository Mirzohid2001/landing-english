# «Umrbod access» → «Study plan» (landing copy + settings).

from django.db import migrations, models

SETTINGS = {
    'base_price_label': 'Platforma + jonli darslar — study plan',
    'pricing_card_title': 'Study plan',
    'reassurance_text': 'Bir martalik to‘lov • Jonli darslar • Study plan',
}

BENEFIT = {
    'icon': 'fas fa-clipboard-list',
    'title': 'Study plan',
    'text': 'Shaxsiy study plan — bosqichma-bosqich tayyorgarlik yo‘li.',
    'badge': 'Plan',
}


def forwards(apps, schema_editor):
    LandingSettings = apps.get_model('blog', 'LandingSettings')
    LandingBenefitCard = apps.get_model('blog', 'LandingBenefitCard')
    LandingSectionCopy = apps.get_model('blog', 'LandingSectionCopy')
    FAQ = apps.get_model('blog', 'FAQ')
    Course = apps.get_model('blog', 'Course')

    LandingSettings.objects.all().update(**SETTINGS)

    LandingBenefitCard.objects.filter(title__icontains='Umrbod').update(**BENEFIT)
    LandingBenefitCard.objects.filter(badge='Lifetime').update(**BENEFIT)
    LandingBenefitCard.objects.filter(title='Study plan').update(**BENEFIT)

    LandingSectionCopy.objects.filter(section='benefits').update(
        subtitle='Jonli darslar, video kurslar, AI checker va study plan — bir joyda.',
    )

    FAQ.objects.filter(question='Bu oylik to‘lovmi?').update(
        answer='Yo‘q. Bir martalik to‘lov. Platformaga kirish va study plan beriladi.',
    )
    FAQ.objects.filter(question='Umrbod access nimani anglatadi?').update(
        question='Study plan nimani anglatadi?',
        answer=(
            'Study plan — siz uchun tuzilgan bosqichma-bosqich tayyorgarlik rejasi. '
            'Platformadagi darslar va mashqlar shu reja asosida ketma-ket beriladi.'
        ),
    )
    FAQ.objects.filter(question='Study plan nimani anglatadi?').update(
        answer=(
            'Study plan — siz uchun tuzilgan bosqichma-bosqich tayyorgarlik rejasi. '
            'Platformadagi darslar va mashqlar shu reja asosida ketma-ket beriladi.'
        ),
    )

    Course.objects.filter(duration__iexact='Umrbod').update(duration='Study plan')


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0029_remove_landing_prices_copy'),
    ]

    operations = [
        migrations.AlterField(
            model_name='landingsettings',
            name='base_price_label',
            field=models.CharField(
                default='Platforma + jonli darslar — study plan',
                max_length=120,
            ),
        ),
        migrations.AlterField(
            model_name='landingsettings',
            name='pricing_card_title',
            field=models.CharField(default='Study plan', max_length=120),
        ),
        migrations.AlterField(
            model_name='landingsettings',
            name='reassurance_text',
            field=models.CharField(
                default='Bir martalik to‘lov • Jonli darslar • Study plan',
                max_length=200,
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
