from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mock_tests', '0005_matching_listening_types'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mocktest',
            name='test_type',
            field=models.CharField(
                choices=[
                    ('reading', 'Reading'),
                    ('listening', 'Listening'),
                    ('writing', 'Writing'),
                    ('speaking', 'Speaking'),
                ],
                max_length=20,
                verbose_name='Test turi',
            ),
        ),
    ]
