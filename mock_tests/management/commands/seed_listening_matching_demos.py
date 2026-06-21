from django.core.management.base import BaseCommand

from mock_tests.models import MockPassage, MockQuestion, MockTest


class Command(BaseCommand):
    help = 'Listening (audio timestamp) va Reading matching demo testlari'

    def handle(self, *args, **options):
        self._listening_demo()
        self._reading_matching_demo()
        self.stdout.write(self.style.SUCCESS('Listening + Matching demo testlar tayyor.'))

    def _listening_demo(self):
        test, _ = MockTest.objects.update_or_create(
            title='Listening Demo — Timestamps & Notes',
            defaults={
                'test_type': 'listening',
                'difficulty': 'medium',
                'description': 'Audio vaqti va notes completion demo. Admin orqali MP3 yuklang.',
                'duration_minutes': 30,
                'passing_score': 60,
                'is_active': True,
            },
        )
        test.questions.all().delete()

        specs = [
            (1, 1, 'notes_completion', 0, 'Hotel booking: Name [1], Check-in [2]', ['riverside', '15 march'], 'ONE WORD AND/OR A NUMBER'),
            (2, 1, 'fill_blank', 45, 'The tour starts at ______ AM.', ['9', 'nine'], 'NO MORE THAN ONE WORD'),
            (3, 1, 'mcq', 90, 'The guide recommends visiting:', [], ''),
            (4, 1, 'mcq', 120, 'Which TWO facilities are included in the ticket?', [], 'Choose TWO answers.'),
            (5, 2, 'notes_completion', 150, 'Workshop venue: Room [1], Floor [2]', ['b', '3'], ''),
            (6, 2, 'fill_blank', 180, 'Participants must bring ______.', ['laptop', 'a laptop'], ''),
        ]
        for order, part, qtype, ts, text, answers, instr in specs:
            q = MockQuestion(
                test=test,
                order=order,
                part_number=part,
                question_type=qtype,
                instruction=instr,
                question_text=text,
                audio_timestamp=ts,
                points=1,
            )
            if qtype == 'mcq' and order == 3:
                q.option_a = 'The museum'
                q.option_b = 'The park'
                q.option_c = 'The library'
                q.option_d = 'The stadium'
                q.option_e = 'The cinema'
                q.option_f = 'The gallery'
                q.option_g = 'The sports centre'
                q.option_h = 'The market'
                q.correct_answer = 'b'
            elif qtype == 'mcq' and order == 4:
                q.mcq_select_count = 2
                q.option_a = 'Audio guide'
                q.option_b = 'Free map'
                q.option_c = 'Lunch voucher'
                q.option_d = 'Parking pass'
                q.option_e = 'Gift shop discount'
                q.correct_answer = 'a,c'
            else:
                q.correct_answers_json = answers
            q.save()

        self.stdout.write(f'  Listening: /courses/tests/{test.pk}/ (MP3 admin dan yuklang)')

    def _reading_matching_demo(self):
        test, _ = MockTest.objects.update_or_create(
            title='Reading Demo — Matching Headings',
            defaults={
                'test_type': 'reading',
                'difficulty': 'medium',
                'description': 'Matching headings va features demo.',
                'duration_minutes': 20,
                'passing_score': 60,
                'is_active': True,
            },
        )
        test.passages.all().delete()
        test.questions.all().delete()

        MockPassage.objects.create(
            test=test,
            order=1,
            title='Urban Green Spaces',
            text=(
                'Paragraph A discusses the history of city parks. '
                'Paragraph B explains health benefits for residents. '
                'Paragraph C covers funding challenges for local councils.'
            ),
        )

        headings_q = MockQuestion(
            test=test,
            order=1,
            part_number=1,
            question_type='matching_headings',
            instruction='Choose the correct heading for each paragraph.',
            question_text='Match headings to paragraphs A–C.',
            points=3,
        )
        headings_q.options_json = {
            'items': [
                {'num': 14, 'label': 'Paragraph A'},
                {'num': 15, 'label': 'Paragraph B'},
                {'num': 16, 'label': 'Paragraph C'},
            ],
            'headings': [
                {'letter': 'i', 'text': 'Origins of public parks'},
                {'letter': 'ii', 'text': 'Wellbeing in crowded cities'},
                {'letter': 'iii', 'text': 'Budget limits on maintenance'},
                {'letter': 'iv', 'text': 'Unused option'},
            ],
        }
        headings_q.correct_answers_json = {'14': 'i', '15': 'ii', '16': 'iii'}
        headings_q.save()

        features_q = MockQuestion(
            test=test,
            order=2,
            part_number=1,
            question_type='matching_features',
            instruction='Match each statement with the correct person A–C.',
            question_text='Who is responsible for each role?',
            points=2,
        )
        features_q.options_json = {
            'items': [
                {'num': 1, 'label': 'Designed the new garden layout'},
                {'num': 2, 'label': 'Organised community volunteers'},
            ],
            'options': [
                {'letter': 'a', 'text': 'Dr. Ellis'},
                {'letter': 'b', 'text': 'Ms. Chen'},
                {'letter': 'c', 'text': 'Mr. Ortiz'},
            ],
        }
        features_q.correct_answers_json = {'1': 'a', '2': 'b'}
        features_q.save()

        self.stdout.write(f'  Reading matching: /courses/tests/{test.pk}/')
