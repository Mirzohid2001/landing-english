from django.core.management.base import BaseCommand

from mock_tests.models import MockQuestion
from mock_tests.question_admin_helpers import fix_misplaced_instruction, sync_points_from_slots


class Command(BaseCommand):
    help = "Savollarda ballni slot soniga tenglashtirish va noto'g'ri ko'rsatmalarni tuzatish"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='O\'zgarishlarni ko\'rsatadi, lekin saqlamaydi',
        )
        parser.add_argument(
            '--test-id',
            type=int,
            default=None,
            help='Faqat shu test ID dagi savollar',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        test_id = options.get('test_id')
        qs = MockQuestion.objects.all().select_related('test')
        if test_id:
            qs = qs.filter(test_id=test_id)

        instr_fixed = 0
        points_fixed = 0
        for q in qs:
            before_points = q.points
            instr_changed = fix_misplaced_instruction(q)
            points_changed = sync_points_from_slots(q)
            if not instr_changed and not points_changed:
                continue
            if instr_changed:
                instr_fixed += 1
                self.stdout.write(
                    f'  #{q.pk} ({q.test.title} — order {q.order}): ko\'rsatma tuzatildi'
                )
            if points_changed:
                points_fixed += 1
                self.stdout.write(
                    f'  #{q.pk} ({q.test.title} — order {q.order}): '
                    f'ball {before_points} → {q.points}'
                )
            if not dry_run:
                q.save(update_fields=['instruction', 'question_text', 'points'])

        verb = 'topildi (dry-run)' if dry_run else 'tuzatildi'
        self.stdout.write(self.style.SUCCESS(
            f'Ko\'rsatma: {instr_fixed} ta {verb}. Ball: {points_fixed} ta {verb}.'
        ))
