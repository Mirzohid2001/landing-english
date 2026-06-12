from django.core.management.base import BaseCommand
from mock_tests.models import MockTest, MockPassage, MockQuestion


class Command(BaseCommand):
    help = 'Phase 4 demo: summary_box va speaking savollar'

    def handle(self, *args, **options):
        self._add_summary_to_reading_demo()
        self._create_speaking_demo()

    def _add_summary_to_reading_demo(self):
        test = MockTest.objects.filter(title='Becoming an Expert — Reading Demo').first()
        if not test:
            self.stdout.write(self.style.WARNING('Reading Demo topilmadi — avval seed_demo_test ishga tushiring'))
            return

        summary_questions = [
            {
                'order': 6,
                'part_number': 1,
                'question_type': 'summary_box',
                'instruction': 'Complete the summary using words from the box below.',
                'question_text': (
                    'Experts believe that [1] practice and feedback lead to [2] performance. '
                    'Novices must first learn key [3] before they can perform tasks confidently.'
                ),
                'correct_answers_json': ['deliberate', 'better', 'terms'],
                'options_json': {
                    'word_list': ['deliberate', 'better', 'terms', 'mental models', 'luck'],
                },
                'explanation': 'Passage: deliberate practice, better performance, key terms.',
            },
            {
                'order': 7,
                'part_number': 1,
                'question_type': 'summary_box',
                'instruction': 'Complete the summary. Choose NO MORE THAN TWO WORDS for each gap.',
                'question_text': (
                    'With experience, people develop [1] that help them recognise patterns. '
                    'Experts can [2] their knowledge to new situations.'
                ),
                'correct_answers_json': ['mental models', 'adapt'],
                'options_json': {
                    'word_list': ['mental models', 'adapt', 'ignore', 'reduce'],
                },
            },
        ]

        added = 0
        updated = 0
        for q in summary_questions:
            _, created = MockQuestion.objects.update_or_create(
                test=test, order=q['order'], defaults=q,
            )
            if created:
                added += 1
            else:
                updated += 1

        total = test.questions.filter(question_type='summary_box').count()
        if added:
            msg = f'Reading Demo ga {added} ta yangi summary_box qo\'shildi'
        else:
            msg = f'Reading Demo: {total} ta summary_box allaqachon mavjud (yangilandi: {updated})'
        self.stdout.write(self.style.SUCCESS(f'{msg} — /courses/tests/{test.pk}/'))

    def _create_speaking_demo(self):
        test, created = MockTest.objects.get_or_create(
            title='Speaking Demo — Part 1',
            defaults={
                'test_type': 'writing',
                'difficulty': 'easy',
                'description': 'Speaking savollarini demo rejimda matn ko\'rinishida javob bering.',
                'duration_minutes': 15,
                'passing_score': 60,
                'is_active': True,
            },
        )

        if not created and test.questions.filter(question_type='speaking').exists():
            self.stdout.write(self.style.WARNING(
                f'Speaking Demo allaqachon mavjud — /courses/tests/{test.pk}/'
            ))
            return

        questions = [
            {
                'order': 1,
                'part_number': 1,
                'question_type': 'speaking',
                'instruction': 'Part 1: Introduction and Interview',
                'question_text': 'Describe your hometown. What do you like most about it?',
                'explanation': 'Demo: kamida 20 belgi yozilgan javob qabul qilinadi.',
            },
            {
                'order': 2,
                'part_number': 1,
                'question_type': 'speaking',
                'instruction': 'Part 1: Introduction and Interview',
                'question_text': 'Do you prefer studying alone or with others? Why?',
            },
        ]

        for q in questions:
            MockQuestion.objects.update_or_create(test=test, order=q['order'], defaults=q)

        self.stdout.write(self.style.SUCCESS(
            f'Speaking Demo tayyor — /courses/tests/{test.pk}/'
        ))
