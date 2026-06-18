"""
Barcha demo mock testlarni bazaga qo'shish.

Ishlatish:
    python manage.py seed_mock_tests
    python manage.py seed_mock_tests --reset
    python manage.py seed_mock_tests --list
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand

from mock_tests.models import MockTest

# Barcha seed_* commandlar yaratadigan test sarlavhalari
DEMO_TEST_TITLES = [
    'Becoming an Expert — Reading Demo',
    'Writing Task Demo',
    'Listening Part 1 Demo',
    'Full Reading Mock Test (40 Questions)',
    'Listening Demo — Timestamps & Notes',
    'Reading Demo — Matching Headings',
]


class Command(BaseCommand):
    help = "Barcha demo mock testlarni bazaga qo'shadi (reading, listening, writing)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Avval demo testlarni o\'chirib, keyin qayta yaratish',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Qaysi commandlar ishlayishini ko\'rsatish (bazaga yozmaydi)',
        )

    def handle(self, *args, **options):
        steps = [
            ('seed_demo_test', 'Reading demo (qisqa)'),
            ('seed_phase2_demos', 'Writing + Listening Part 1'),
            ('seed_phase3_full_reading', 'To\'liq Reading (40 savol)'),
            ('seed_phase4_demos', 'Summary box (Reading)'),
            ('seed_listening_matching_demos', 'Listening timestamps + Matching headings'),
        ]

        if options['list']:
            self.stdout.write('Quyidagi bosqichlar bajariladi:\n')
            for cmd, label in steps:
                self.stdout.write(f'  • {cmd} — {label}')
            self.stdout.write(f'\nJami {len(DEMO_TEST_TITLES)} ta demo test yaratiladi/yangilanadi.')
            return

        if options['reset']:
            deleted, _ = MockTest.objects.filter(title__in=DEMO_TEST_TITLES).delete()
            self.stdout.write(self.style.WARNING(f'{deleted} ta obyekt o\'chirildi (demo testlar).'))

        self.stdout.write(self.style.MIGRATE_HEADING('Demo testlar qo\'shilmoqda...\n'))

        for cmd, label in steps:
            self.stdout.write(f'  → {label} ({cmd})...')
            call_command(cmd, verbosity=0)

        self.stdout.write('')
        tests = MockTest.objects.filter(title__in=DEMO_TEST_TITLES, is_active=True).order_by('test_type', 'title')
        self.stdout.write(self.style.SUCCESS(f'Tayyor! Faol demo testlar: {tests.count()} ta\n'))
        for t in tests:
            self.stdout.write(
                f'  [{t.get_test_type_display():9}] {t.title} — {t.questions.count()} savol (id={t.pk})'
            )
        self.stdout.write('')
        self.stdout.write('Listening testlarga admin orqali MP3 audio yuklang.')
        self.stdout.write('Sayt: /courses/')
