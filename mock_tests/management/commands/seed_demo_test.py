from django.core.management.base import BaseCommand
from mock_tests.models import MockTest, MockPassage, MockQuestion


class Command(BaseCommand):
    help = "Demo Reading test yaratadi"

    def handle(self, *args, **options):
        test, created = MockTest.objects.get_or_create(
            title='Becoming an Expert — Reading Demo',
            defaults={
                'test_type': 'reading',
                'difficulty': 'medium',
                'description': 'IELTS Reading formatidagi demo test. Part 1: savollar 1-5.',
                'duration_minutes': 20,
                'passing_score': 60,
                'is_active': True,
            },
        )
        if not created and test.questions.exists():
            self.stdout.write(self.style.WARNING('Demo test allaqachon mavjud'))
            return

        passage_text = """Becoming an Expert

Expertise is often defined as extensive knowledge and skills in a particular field. Researchers have studied how novices become experts through years of deliberate practice and feedback.

Novices must learn the key terms and rules of tasks before performing them confidently. With experience, people develop mental models that help them recognize patterns quickly. Experts can also adapt their knowledge to new situations more effectively than beginners.

Studies show that expert performance is not simply the result of talent. Continuous practice, coaching, and reflection are essential. Even highly skilled professionals continue learning throughout their careers."""

        MockPassage.objects.get_or_create(
            test=test, order=1,
            defaults={'title': 'Passage 1', 'text': passage_text},
        )

        questions = [
            {
                'order': 1, 'part_number': 1, 'question_type': 'fill_blank',
                'instruction': 'Choose NO MORE THAN THREE WORDS from the passage for each answer.',
                'question_text': 'Novices have to learn the key ______ and rules of tasks before performing them.',
                'correct_answer': 'terms', 'correct_answers_json': ['terms/key terms'],
            },
            {
                'order': 2, 'part_number': 1, 'question_type': 'fill_blank',
                'instruction': 'Choose NO MORE THAN THREE WORDS from the passage for each answer.',
                'question_text': 'With experience, people develop ______ that help them recognize patterns.',
                'correct_answer': 'mental models',
            },
            {
                'order': 3, 'part_number': 1, 'question_type': 'true_false_not_given',
                'question_text': 'Experts never need to continue learning after becoming skilled.',
                'correct_answer': 'b',
            },
            {
                'order': 4, 'part_number': 1, 'question_type': 'mcq',
                'question_text': 'According to the passage, expert performance is mainly the result of:',
                'option_a': 'Talent alone', 'option_b': 'Deliberate practice and feedback',
                'option_c': 'Luck', 'option_d': 'Short training courses',
                'correct_answer': 'b',
            },
            {
                'order': 5, 'part_number': 1, 'question_type': 'fill_blank',
                'question_text': 'Continuous practice, coaching, and ______ are essential.',
                'correct_answer': 'reflection',
            },
        ]

        for q in questions:
            MockQuestion.objects.update_or_create(test=test, order=q['order'], defaults=q)

        self.stdout.write(self.style.SUCCESS(f'Demo test tayyor: /courses/tests/{test.pk}/'))
