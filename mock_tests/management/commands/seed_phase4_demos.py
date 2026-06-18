from django.core.management.base import BaseCommand
from mock_tests.models import MockTest, MockQuestion


class Command(BaseCommand):
    help = 'Phase 4 demo: Reading uchun summary_box savollar'

    def handle(self, *args, **options):
        self._add_summary_to_reading_demo()
        self._remove_speaking_demo()

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

    def _remove_speaking_demo(self):
        deleted, _ = MockTest.objects.filter(title='Speaking Demo — Part 1').delete()
        deactivated = MockTest.objects.filter(test_type='speaking').update(is_active=False)
        if deleted or deactivated:
            self.stdout.write(self.style.SUCCESS(
                f'Speaking demo olib tashlandi (o\'chirildi: {deleted}, o\'chirilgan: {deactivated})'
            ))
