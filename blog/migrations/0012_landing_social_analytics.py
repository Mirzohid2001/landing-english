from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0011_landing_hero_copy'),
    ]

    operations = [
        migrations.AddField(
            model_name='landingsettings',
            name='ga4_measurement_id',
            field=models.CharField(
                blank=True,
                help_text='Google Analytics 4 ID (masalan G-XXXXXXXX). Bo‘sh bo‘lsa o‘lchov yoqilmaydi.',
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name='landingsettings',
            name='instagram_url',
            field=models.URLField(blank=True, default='https://instagram.com/tonacademy'),
        ),
        migrations.AddField(
            model_name='landingsettings',
            name='support_hours',
            field=models.CharField(blank=True, default='Dush–Shan: 09:00–20:00', max_length=120),
        ),
        migrations.AddField(
            model_name='landingsettings',
            name='youtube_url',
            field=models.URLField(blank=True, default='https://youtube.com/@tonacademy'),
        ),
    ]
