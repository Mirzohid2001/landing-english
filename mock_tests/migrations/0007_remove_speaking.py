from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mock_tests', '0006_speaking_test_type'),
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
                ],
                max_length=20,
                verbose_name='Test turi',
            ),
        ),
        migrations.AlterField(
            model_name='mockquestion',
            name='question_type',
            field=models.CharField(
                choices=[
                    ('mcq', 'Multiple Choice (A/B/C/D)'),
                    ('true_false_not_given', 'True / False / Not Given'),
                    ('yes_no_not_given', 'Yes / No / Not Given'),
                    ('fill_blank', "Bo'sh joyni to'ldirish"),
                    ('sentence_completion', 'Sentence Completion'),
                    ('essay', 'Essay (Writing)'),
                    ('summary_completion', 'Summary Completion'),
                    ('matching', 'Matching (bitta tanlov — eski)'),
                    ('matching_headings', 'Matching Headings'),
                    ('matching_features', 'Matching Features'),
                    ('matching_info', 'Matching Information'),
                    ('matching_sentences', 'Matching Sentence Endings'),
                    ('classification', 'Classification'),
                    ('summary_box', 'Summary + box (inline qavslar)'),
                    ('notes_completion', 'Notes Completion (Listening)'),
                    ('table_completion', 'Table Completion'),
                ],
                default='mcq',
                max_length=30,
                verbose_name='Savol turi',
            ),
        ),
    ]
