from django.core.management.base import BaseCommand
from mock_tests.models import MockTest, MockPassage, MockQuestion


class Command(BaseCommand):
    help = 'Phase 2 demo testlar: Writing va kengaytirilgan Reading'

    def handle(self, *args, **options):
        # Writing demo
        writing, _ = MockTest.objects.get_or_create(
            title='Writing Task Demo',
            test_type='writing',
            defaults={
                'difficulty': 'medium',
                'description': 'IELTS Writing formatida 2 ta task (demo). Essay kamida 50 belgi.',
                'duration_minutes': 40,
                'passing_score': 50,
                'is_active': True,
            },
        )
        if not writing.questions.exists():
            MockQuestion.objects.bulk_create([
                MockQuestion(
                    test=writing, order=1, part_number=1, question_type='essay',
                    instruction='Write at least 150 words.',
                    question_text='Some people believe that technology makes life easier. Others think it creates new problems.\n\nDiscuss both views and give your own opinion.',
                    points=1,
                ),
                MockQuestion(
                    test=writing, order=2, part_number=1, question_type='essay',
                    instruction='Write at least 250 words.',
                    question_text='In many countries, the number of people studying at university is increasing.\n\nWhat are the causes of this trend? Is it positive or negative?',
                    points=1,
                ),
            ])
            self.stdout.write(self.style.SUCCESS('Writing demo yaratildi'))

        # Reading Part 2 expansion on existing test
        reading = MockTest.objects.filter(test_type='reading').first()
        if reading:
            MockPassage.objects.get_or_create(
                test=reading, order=2,
                defaults={
                    'title': 'Passage 2 — Urban Farming',
                    'text': '''Urban farming has grown rapidly in cities worldwide. Rooftop gardens and community plots allow residents to grow fresh vegetables close to home.

Supporters argue that urban farming reduces food transport costs and improves access to healthy food in low-income neighborhoods. Critics note that space is limited and yields are often small compared to rural agriculture.

Despite challenges, many cities now include urban agriculture in their sustainability plans.''',
                },
            )
            if not reading.questions.filter(order=6).exists():
                MockQuestion.objects.bulk_create([
                    MockQuestion(
                        test=reading, order=6, part_number=2, question_type='yes_no_not_given',
                        question_text='Urban farming always produces more food than rural farms.',
                        correct_answer='b', points=1,
                    ),
                    MockQuestion(
                        test=reading, order=7, part_number=2, question_type='fill_blank',
                        instruction='Choose NO MORE THAN TWO WORDS from the passage.',
                        question_text='Supporters say urban farming improves access to ______ food.',
                        correct_answer='healthy', correct_answers_json=['healthy/nutritious'],
                        points=1,
                    ),
                ])
                self.stdout.write(self.style.SUCCESS(f'Reading test kengaytirildi: /courses/tests/{reading.pk}/'))

        # Listening demo (audio admin orqali qo'shiladi)
        listening, created = MockTest.objects.get_or_create(
            title='Listening Part 1 Demo',
            test_type='listening',
            defaults={
                'difficulty': 'easy',
                'description': 'Listening demo. Admin paneldan MP3 audio fayl yuklang.',
                'duration_minutes': 15,
                'passing_score': 60,
                'is_active': True,
            },
        )
        if created or not listening.questions.exists():
            MockQuestion.objects.filter(test=listening).delete()
            MockQuestion.objects.bulk_create([
                MockQuestion(
                    test=listening, order=1, part_number=1, question_type='fill_blank',
                    instruction='Write ONE WORD AND/OR A NUMBER.',
                    question_text='Customer name: ______',
                    correct_answer='Johnson', correct_answers_json=['Johnson/johnson'],
                    audio_timestamp=0, points=1,
                ),
                MockQuestion(
                    test=listening, order=2, part_number=1, question_type='fill_blank',
                    question_text='Phone number: ______',
                    correct_answer='914112561', audio_timestamp=15, points=1,
                ),
                MockQuestion(
                    test=listening, order=3, part_number=1, question_type='mcq',
                    question_text='Preferred contact method:',
                    option_a='Email', option_b='Phone', option_c='Telegram', option_d='SMS',
                    correct_answer='b', audio_timestamp=30, points=1,
                ),
            ])
            self.stdout.write(self.style.WARNING(
                f'Listening demo: /courses/tests/{listening.pk}/ — admin orqali audio fayl yuklang!'
            ))

        self.stdout.write(self.style.SUCCESS('Phase 2 demo testlar tayyor'))
