from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0027_instagram_tonacademyuz'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Ixtiyoriy. Bo‘sh qoldirish mumkin.',
                max_digits=10,
                null=True,
            ),
        ),
    ]
