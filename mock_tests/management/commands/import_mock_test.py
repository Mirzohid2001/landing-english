import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from mock_tests.models import MockTest, MockPassage, MockQuestion


class Command(BaseCommand):
    help = 'JSON fayldan MockTest import qiladi'

    def add_arguments(self, parser):
        parser.add_argument('json_path', type=str, help='Test JSON fayl yo\'li')
        parser.add_argument(
            '--update',
            action='store_true',
            help='Mavjud testni title bo\'yicha yangilash',
        )

    def handle(self, *args, **options):
        path = Path(options['json_path'])
        if not path.exists():
            raise CommandError(f'Fayl topilmadi: {path}')

        with open(path, encoding='utf-8') as f:
            data = json.load(f)

        title = data.get('title')
        if not title:
            raise CommandError('JSON da "title" majburiy')

        test_fields = {
            'test_type': data.get('test_type', 'reading'),
            'difficulty': data.get('difficulty', 'medium'),
            'description': data.get('description', ''),
            'duration_minutes': data.get('duration_minutes'),
            'passing_score': data.get('passing_score', 60),
            'is_active': data.get('is_active', True),
        }

        if options['update']:
            test, created = MockTest.objects.update_or_create(
                title=title, defaults=test_fields,
            )
            if not created:
                test.passages.all().delete()
                test.questions.all().delete()
        else:
            existing = MockTest.objects.filter(title=title).first()
            if existing:
                self.stdout.write(self.style.WARNING(
                    f'"{title}" allaqachon mavjud (id={existing.pk}). '
                    f'Yangilash uchun: python manage.py import_mock_test {path} --update'
                ))
                return
            test = MockTest.objects.create(title=title, **test_fields)

        for passage in data.get('passages', []):
            MockPassage.objects.create(
                test=test,
                order=passage.get('order', 1),
                title=passage.get('title', ''),
                text=passage.get('text', ''),
            )

        for q in data.get('questions', []):
            MockQuestion.objects.create(
                test=test,
                order=q.get('order', 0),
                part_number=q.get('part_number', 1),
                question_type=q.get('question_type', 'mcq'),
                instruction=q.get('instruction', ''),
                question_text=q.get('question_text', ''),
                option_a=q.get('option_a', ''),
                option_b=q.get('option_b', ''),
                option_c=q.get('option_c', ''),
                option_d=q.get('option_d', ''),
                correct_answer=q.get('correct_answer', ''),
                correct_answers_json=q.get('correct_answers_json', q.get('correct_answer_json', [])),
                options_json=q.get('options_json', {}),
                explanation=q.get('explanation', ''),
                points=q.get('points', 1),
                audio_timestamp=q.get('audio_timestamp'),
            )

        self.stdout.write(self.style.SUCCESS(
            f'Import tayyor: "{test.title}" — {test.questions.count()} savol, '
            f'/courses/tests/{test.pk}/'
        ))
