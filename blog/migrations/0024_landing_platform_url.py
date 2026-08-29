from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0023_disable_announcement_bar'),
    ]

    operations = [
        migrations.AddField(
            model_name='landingsettings',
            name='platform_url',
            field=models.URLField(
                default='https://tonielts.uz/',
                help_text='«Sistemaga o‘tish» tugmasi — o‘quv platformasi (login).',
            ),
        ),
    ]
