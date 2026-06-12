from django.core.management.base import BaseCommand
from mock_tests.models import MockTest, MockPassage, MockQuestion

PASSAGES = [
    {
        'order': 1,
        'title': 'Passage 1 — Becoming an Expert',
        'text': '''Researchers have long studied how novices become experts. Novices must learn key terms and rules before performing tasks confidently. With experience, people develop mental models that help them recognize patterns quickly.

Experts adapt their knowledge to new situations more effectively than beginners. Studies show that expert performance results from deliberate practice, coaching, and reflection rather than talent alone.''',
    },
    {
        'order': 2,
        'title': 'Passage 2 — Urban Farming',
        'text': '''Urban farming has grown rapidly in cities worldwide. Rooftop gardens and community plots allow residents to grow fresh vegetables close to home. Supporters argue that urban farming reduces transport costs and improves access to healthy food.

Critics note that space is limited and yields are often small. Despite challenges, many cities include urban agriculture in sustainability plans.''',
    },
    {
        'order': 3,
        'title': 'Passage 3 — Ocean Plastic',
        'text': '''Plastic pollution in oceans threatens marine ecosystems. Microplastics enter the food chain and affect fish populations. International agreements aim to reduce single-use plastics, but enforcement remains difficult.

Scientists recommend combining policy change with consumer education. Biodegradable alternatives are being developed, though cost remains a barrier for widespread adoption.''',
    },
]


class Command(BaseCommand):
    help = '40 savolli to\'liq Reading mock test (3 passage)'

    def handle(self, *args, **options):
        test, created = MockTest.objects.get_or_create(
            title='Full Reading Mock Test (40 Questions)',
            test_type='reading',
            defaults={
                'difficulty': 'hard',
                'description': 'IELTS Reading format: 3 passage, 40 savol, 60 daqiqa. Band score natijada ko\'rsatiladi.',
                'duration_minutes': 60,
                'passing_score': 60,
                'is_active': True,
            },
        )
        if not created and test.questions.count() >= 40:
            self.stdout.write(self.style.WARNING(f'Test allaqachon to\'liq: /courses/tests/{test.pk}/'))
            return

        test.questions.all().delete()
        test.passages.all().delete()

        for p in PASSAGES:
            MockPassage.objects.create(test=test, order=p['order'], title=p['title'], text=p['text'])

        order = 1
        for part in (1, 2, 3):
            part_q_count = 13 if part < 3 else 14
            for i in range(part_q_count):
                qtype = 'fill_blank'
                if i % 5 == 4:
                    qtype = 'true_false_not_given'
                elif i % 7 == 6:
                    qtype = 'matching'
                elif i % 9 == 8:
                    qtype = 'summary_completion'

                q = MockQuestion(
                    test=test,
                    order=order,
                    part_number=part,
                    question_type=qtype,
                    instruction='Choose NO MORE THAN TWO WORDS from the passage.' if qtype != 'true_false_not_given' else '',
                    question_text=f'Question {order}: Sample item for Part {part}.',
                    points=1,
                )
                if qtype == 'true_false_not_given':
                    q.correct_answer = 'a' if order % 2 else 'c'
                elif qtype == 'matching':
                    q.options_json = {
                        'options': [
                            {'letter': 'a', 'text': f'Heading option A for Q{order}'},
                            {'letter': 'b', 'text': f'Heading option B for Q{order}'},
                            {'letter': 'c', 'text': f'Heading option C for Q{order}'},
                            {'letter': 'd', 'text': f'Heading option D for Q{order}'},
                        ]
                    }
                    q.correct_answer = 'b'
                else:
                    q.correct_answer = 'practice' if order % 2 else 'experts'
                    q.correct_answers_json = [q.correct_answer, 'mental models', 'urban farming']
                q.save()
                order += 1

        self.stdout.write(self.style.SUCCESS(
            f'Full Reading test tayyor: {test.total_questions} savol — /courses/tests/{test.pk}/'
        ))
