# Landingdan narx matnlarini olib tashlash (section copy + FAQ).

from django.db import migrations

BENEFITS = {
    'kicker': 'Nimalar olasiz?',
    'title': 'Platformada nimalar olasiz?',
    'subtitle': 'Jonli darslar, video kurslar, AI checker — bir martalik to‘lov bilan umrbod access.',
}

FAQ_UPDATES = {
    'Bu oylik to‘lovmi?': (
        'Yo‘q. Bir martalik to‘lov. Umrbod platformaga kirish huquqi beriladi.'
    ),
    '599 000 so‘mga aynan nimalar kiradi?': (
        'Jonli darslar, 100+ video darslar, AI checker, Reading/Listening/Writing '
        'materiallari, progress tracking va barcha yangilanishlar.'
    ),
    'Platformaga aynan nimalar kiradi?': (
        'Jonli darslar, 100+ video darslar, AI checker, Reading/Listening/Writing '
        'materiallari, progress tracking va barcha yangilanishlar.'
    ),
    'Jonli darslar bormi?': (
        'Ha, jonli darslar mavjud. Qo‘shimcha LIVE bundle da Speaking + Reading '
        'LIVE darslar kengaytirilgan formatda beriladi.'
    ),
    'Speaking bormi?': (
        'Ha, jonli darslar orqali Speaking amaliyoti bor. LIVE bundle da Speaking + '
        'Reading LIVE darslar alohida kengaytirilgan paket sifatida taklif etiladi.'
    ),
}


def forwards(apps, schema_editor):
    LandingSectionCopy = apps.get_model('blog', 'LandingSectionCopy')
    FAQ = apps.get_model('blog', 'FAQ')
    ProcessStep = apps.get_model('blog', 'ProcessStep')

    LandingSectionCopy.objects.filter(section='benefits').update(**BENEFITS)

    FAQ.objects.filter(question='Bu oylik to‘lovmi?').update(
        answer=FAQ_UPDATES['Bu oylik to‘lovmi?'],
    )
    FAQ.objects.filter(question='Jonli darslar bormi?').update(
        answer=FAQ_UPDATES['Jonli darslar bormi?'],
    )
    FAQ.objects.filter(question='Speaking bormi?').update(
        answer=FAQ_UPDATES['Speaking bormi?'],
    )
    FAQ.objects.filter(question='599 000 so‘mga aynan nimalar kiradi?').update(
        question='Platformaga aynan nimalar kiradi?',
        answer=FAQ_UPDATES['Platformaga aynan nimalar kiradi?'],
    )
    FAQ.objects.filter(question='Platformaga aynan nimalar kiradi?').update(
        answer=FAQ_UPDATES['Platformaga aynan nimalar kiradi?'],
    )

    ProcessStep.objects.filter(
        flow='purchase',
        step_number=2,
        description__icontains='599',
    ).update(description='Qaysi paket kerakligini yozing.')


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0028_course_price_optional'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
