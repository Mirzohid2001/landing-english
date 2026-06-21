from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mock_tests', '0008_mockquestion_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='mockquestion',
            name='option_e',
            field=models.CharField(blank=True, max_length=500, verbose_name='Variant E'),
        ),
        migrations.AddField(
            model_name='mockquestion',
            name='option_f',
            field=models.CharField(blank=True, max_length=500, verbose_name='Variant F'),
        ),
        migrations.AddField(
            model_name='mockquestion',
            name='option_g',
            field=models.CharField(blank=True, max_length=500, verbose_name='Variant G'),
        ),
        migrations.AddField(
            model_name='mockquestion',
            name='option_h',
            field=models.CharField(blank=True, max_length=500, verbose_name='Variant H'),
        ),
        migrations.AddField(
            model_name='mockquestion',
            name='mcq_select_count',
            field=models.PositiveSmallIntegerField(
                default=1,
                help_text='MCQ: 1, 2 yoki 3 ta to\'g\'ri javob (masalan «2 ta javob tanlang»)',
                verbose_name='Tanlash soni',
            ),
        ),
        migrations.AlterField(
            model_name='mockquestion',
            name='correct_answer',
            field=models.CharField(
                blank=True,
                help_text='MCQ: bitta harf (a) yoki vergul bilan (a,c)',
                max_length=200,
                verbose_name="To'g'ri javob",
            ),
        ),
        migrations.AlterField(
            model_name='mockquestion',
            name='question_type',
            field=models.CharField(
                choices=[
                    ('mcq', 'Multiple Choice (A–H)'),
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
