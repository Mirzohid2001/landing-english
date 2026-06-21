from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mock_tests', '0007_remove_speaking'),
    ]

    operations = [
        migrations.AddField(
            model_name='mockquestion',
            name='image',
            field=models.ImageField(
                blank=True,
                help_text='Listening: xarita, jadval yoki diagramma (JPG/PNG, max 5 MB)',
                null=True,
                upload_to='mock_tests/questions/',
                verbose_name='Rasm',
            ),
        ),
    ]
