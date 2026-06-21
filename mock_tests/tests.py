import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from mock_tests.matching_utils import (
    build_matching_fields,
    parse_matching_correct,
    parse_matching_items,
    parse_matching_options,
)
from mock_tests.models import MockAttempt, MockPassage, MockQuestion, MockTest
from mock_tests.services.answer_normalizer import match_text_answer, score_extended_text
from mock_tests.services.band_score import earned_ratio_to_band
from mock_tests.services.gradable import total_gradable_slots
from mock_tests.services.scoring import (
    check_question_answer,
    score_attempt,
    score_blanks,
    score_question_points,
)
from mock_tests.services.stats import get_dashboard_stats


class MockTestFixturesMixin:
    @classmethod
    def _create_listening_test(cls):
        test = MockTest.objects.create(
            title='Test Listening Auto',
            test_type='listening',
            difficulty='medium',
            duration_minutes=30,
            is_active=True,
        )
        MockQuestion.objects.create(
            test=test,
            order=1,
            part_number=1,
            question_type='notes_completion',
            question_text='Name [1], City [2]',
            correct_answers_json=['anna', 'london'],
            audio_timestamp=10.5,
            points=1,
        )
        MockQuestion.objects.create(
            test=test,
            order=2,
            part_number=1,
            question_type='mcq',
            question_text='Pick one',
            option_a='A1',
            option_b='A2',
            option_c='A3',
            option_d='A4',
            correct_answer='b',
            audio_timestamp=60,
            points=1,
        )
        return test

    @classmethod
    def _create_listening_mcq_extended_test(cls):
        test = MockTest.objects.create(
            title='Test Listening MCQ Extended',
            test_type='listening',
            difficulty='medium',
            duration_minutes=30,
            is_active=True,
        )
        MockQuestion.objects.create(
            test=test,
            order=1,
            part_number=1,
            question_type='mcq',
            question_text='The guide recommends visiting:',
            option_a='The museum',
            option_b='The park',
            option_c='The library',
            option_d='The stadium',
            option_e='The cinema',
            option_f='The gallery',
            option_g='The sports centre',
            option_h='The market',
            correct_answer='b',
            audio_timestamp=90,
            points=1,
        )
        MockQuestion.objects.create(
            test=test,
            order=2,
            part_number=1,
            question_type='mcq',
            mcq_select_count=2,
            question_text='Which TWO facilities are included in the ticket?',
            option_a='Audio guide',
            option_b='Free map',
            option_c='Lunch voucher',
            option_d='Parking pass',
            option_e='Gift shop discount',
            correct_answer='a,c',
            audio_timestamp=120,
            points=1,
        )
        return test

    @classmethod
    def _create_reading_matching_test(cls):
        test = MockTest.objects.create(
            title='Test Reading Matching Auto',
            test_type='reading',
            difficulty='medium',
            duration_minutes=20,
            is_active=True,
        )
        MockPassage.objects.create(
            test=test,
            order=1,
            title='P1',
            text='Sample passage text.',
        )
        MockQuestion.objects.create(
            test=test,
            order=1,
            part_number=1,
            question_type='matching_headings',
            question_text='Match headings',
            options_json={
                'items': [
                    {'num': 14, 'label': 'Paragraph A'},
                    {'num': 15, 'label': 'Paragraph B'},
                ],
                'headings': [
                    {'letter': 'i', 'text': 'First'},
                    {'letter': 'ii', 'text': 'Second'},
                ],
            },
            correct_answers_json={'14': 'i', '15': 'ii'},
            points=2,
        )
        MockQuestion.objects.create(
            test=test,
            order=2,
            part_number=1,
            question_type='matching_features',
            question_text='Match people',
            options_json={
                'items': [{'num': 1, 'label': 'Statement one'}],
                'options': [
                    {'letter': 'a', 'text': 'Alice'},
                    {'letter': 'b', 'text': 'Bob'},
                ],
            },
            correct_answers_json={'1': 'a'},
            points=1,
        )
        return test


class AnswerNormalizerTests(TestCase):
    def test_number_word_and_digit(self):
        self.assertTrue(match_text_answer('nine', ['9']))
        self.assertTrue(match_text_answer('9', ['nine']))

    def test_article_stripping(self):
        self.assertTrue(match_text_answer('a laptop', ['laptop']))
        self.assertTrue(match_text_answer('the london', ['london']))

    def test_multiple_acceptable(self):
        self.assertTrue(match_text_answer('riverside', ['riverside', 'riverside hotel']))

    def test_fuzzy_typo(self):
        self.assertTrue(match_text_answer('londn', ['london']))

    def test_extended_text_scoring(self):
        short = score_extended_text('word ' * 10, min_words=20, target_words=120)
        self.assertEqual(short, 0.0)
        mid = score_extended_text('word ' * 60, min_words=50, target_words=250)
        self.assertGreater(mid, 0.5)
        self.assertLess(mid, 1.0)


class MatchingUtilsTests(TestCase):
    def test_parse_matching_lines(self):
        items = parse_matching_items('14|Paragraph A\n15|Paragraph B')
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['num'], 14)
        opts = parse_matching_options('i|Heading one\nii|Heading two', headings_mode=True)
        self.assertEqual(opts[0]['letter'], 'i')
        corr = parse_matching_correct('14:i\n15:ii')
        self.assertEqual(corr, {'14': 'i', '15': 'ii'})

    def test_build_matching_fields_with_saved_answer(self):
        test = MockTestFixturesMixin._create_reading_matching_test()
        q = test.questions.get(question_type='matching_headings')
        fields = build_matching_fields(q, {'14': 'i', '15': 'wrong'})
        self.assertEqual(len(fields), 2)
        self.assertEqual(fields[0]['value'], 'i')
        self.assertEqual(fields[1]['value'], 'wrong')


class ScoringTests(MockTestFixturesMixin, TestCase):
    def test_matching_headings_full_and_partial(self):
        test = self._create_reading_matching_test()
        q = test.questions.get(question_type='matching_headings')
        ok, _, _ = check_question_answer(q, {'14': 'i', '15': 'ii'})
        self.assertTrue(ok)
        ok2, _, _ = check_question_answer(q, {'14': 'i', '15': 'x'})
        self.assertFalse(ok2)

    def test_notes_completion_dict_answers(self):
        test = self._create_listening_test()
        q = test.questions.get(question_type='notes_completion')
        ok, _, _ = check_question_answer(q, {'1': 'anna', '2': 'london'})
        self.assertTrue(ok)
        ok2, _, _ = check_question_answer(q, {'1': 'anna', '2': 'paris'})
        self.assertFalse(ok2)

    def test_notes_partial_credit(self):
        test = self._create_listening_test()
        q = test.questions.get(question_type='notes_completion')
        attempt = MockAttempt.objects.create(
            test=test,
            session_key='partial-notes',
            answers_json={str(q.pk): {'1': 'anna', '2': 'wrong'}},
        )
        result = score_attempt(attempt, [q])
        self.assertEqual(result['earned_points'], 1.0)
        self.assertEqual(result['correct_count'], 1)
        self.assertEqual(len(result['details']), 2)

    def test_fill_blank_number_variant(self):
        test = MockTest.objects.create(
            title='Fill demo',
            test_type='listening',
            is_active=True,
        )
        q = MockQuestion.objects.create(
            test=test,
            order=1,
            question_type='fill_blank',
            question_text='Starts at ______',
            correct_answers_json=['9', 'nine'],
            points=1,
        )
        ok, _, _ = check_question_answer(q, 'nine')
        self.assertTrue(ok)

    def test_score_attempt_partial_matching_points(self):
        test = self._create_reading_matching_test()
        headings = test.questions.get(question_type='matching_headings')
        features = test.questions.get(question_type='matching_features')
        attempt = MockAttempt.objects.create(
            test=test,
            session_key='test-session-partial',
            answers_json={
                str(headings.pk): {'14': 'i', '15': 'wrong'},
                str(features.pk): {'1': 'a'},
            },
        )
        result = score_attempt(attempt, list(test.questions.all()))
        self.assertGreater(float(result['score_percent']), 0)
        self.assertLess(float(result['score_percent']), 100)

    def test_band_uses_earned_ratio(self):
        band = earned_ratio_to_band(1.5, 2.0)
        self.assertGreater(band, 0)


class ModelTests(MockTestFixturesMixin, TestCase):
    def test_notes_ten_blanks_count_as_ten_slots(self):
        test = MockTest.objects.create(
            title='Notes 10 blanks',
            test_type='listening',
            is_active=True,
        )
        text = ' '.join(f'Word [{i}]' for i in range(1, 11))
        answers = [
            '15 October', 'hotel', '175', 'sailing', 'class',
            'golf', 'fishing', 'caravan', 'massage', 'menu',
        ]
        q = MockQuestion.objects.create(
            test=test,
            order=1,
            part_number=1,
            question_type='notes_completion',
            question_text=text,
            correct_answers_json=answers,
            points=1,
        )
        self.assertEqual(q.gradable_slot_count(), 10)
        self.assertEqual(total_gradable_slots([q]), 10)

        attempt = MockAttempt.objects.create(
            test=test,
            session_key='notes-10',
            answers_json={str(q.pk): {'1': '15 October', '2': 'hotel', '3': '511566'}},
        )
        result = score_attempt(attempt, [q])
        self.assertEqual(result['total_questions'], 10)
        self.assertEqual(len(result['details']), 10)
        self.assertEqual(result['correct_count'], 2)
        self.assertGreater(float(result['score_percent']), 0)
        self.assertLess(float(result['score_percent']), 100)

    def test_take_page_shows_gradable_slot_count(self):
        test = MockTest.objects.create(
            title='Notes UI count',
            test_type='listening',
            is_active=True,
        )
        q = MockQuestion.objects.create(
            test=test,
            order=1,
            part_number=1,
            question_type='notes_completion',
            question_text='A [1] B [2] C [3]',
            correct_answers_json=['a', 'b', 'c'],
        )
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('data-total-questions="3"', response.content.decode())
        test = self._create_listening_test()
        q = test.questions.get(question_type='notes_completion')
        blanks = [s for s in q.get_bracket_segments() if s['type'] == 'blank']
        self.assertEqual(len(blanks), 2)

    def test_part_group_audio_start(self):
        from mock_tests.views import _build_part_groups

        test = self._create_listening_test()
        questions = list(test.questions.all())
        groups = _build_part_groups(test, questions, [])
        self.assertEqual(groups[0]['audio_start_time'], 10.5)


class ViewsTests(MockTestFixturesMixin, TestCase):
    def setUp(self):
        self.client = Client()

    def test_take_listening_renders_audio_and_timestamps(self):
        test = self._create_listening_test()
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('data-audio-ts', html)
        self.assertIn('listening-main-card', html)

    def test_part_range_uses_question_order_not_blank_nums(self):
        from mock_tests.views import _build_part_groups

        test = self._create_listening_test()
        MockQuestion.objects.create(
            test=test,
            order=4,
            part_number=2,
            question_type='fill_blank',
            question_text='Part 2 question',
            correct_answer='x',
            points=1,
        )
        questions = list(test.questions.all())
        groups = _build_part_groups(test, questions, [])
        part2 = next(g for g in groups if g['part_number'] == 2)
        self.assertEqual(part2['range_label'], '4')
        self.assertEqual(part2['question_count'], 1)

    def test_take_reading_renders_matching_ui(self):
        test = self._create_reading_matching_test()
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('mock-matching-select', response.content.decode())

    def test_finish_ajax_redirects_to_result(self):
        test = self._create_reading_matching_test()
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        self.client.get(url)
        answers = {}
        for q in test.questions.all():
            if q.is_multi_matching():
                answers[str(q.pk)] = dict(q.correct_answers_json)
        response = self.client.post(
            url,
            data=json.dumps({'action': 'finish', 'answers': answers}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('/result/', data['redirect_url'])

    def test_save_answers_ajax(self):
        test = self._create_listening_test()
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        self.client.get(url)
        q = test.questions.get(question_type='notes_completion')
        response = self.client.post(
            url,
            data=json.dumps({
                'action': 'save',
                'answers': {str(q.pk): {'1': 'anna', '2': 'london'}},
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

    def test_list_shows_last_finished_result_for_session(self):
        test = self._create_listening_test()
        take_url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        self.client.get(take_url)
        session_key = self.client.session.session_key
        MockAttempt.objects.create(
            test=test,
            session_key=session_key,
            is_finished=True,
            score_percent=75,
            correct_count=1,
            total_questions=2,
            ielts_band=6.0,
        )
        list_url = reverse('mock_tests:test_list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('mock-test-last-result', html)
        self.assertIn('75%', html)
        self.assertIn('Band 6.0', html)

    def test_take_has_onboarding_markup(self):
        test = self._create_listening_test()
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        response = self.client.get(url)
        html = response.content.decode()
        self.assertIn('mock-onboarding', html)

    def test_take_listening_audio_progress_when_audio_present(self):
        test = self._create_listening_test()
        test.audio_file.save(
            'demo.mp3',
            SimpleUploadedFile('demo.mp3', b'fake-audio', content_type='audio/mpeg'),
        )
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        response = self.client.get(url)
        html = response.content.decode()
        self.assertIn('audio-progress-track', html)
        self.assertIn('audio-progress-fill', html)

    def test_daily_limit_blocks_new_post_without_in_progress(self):
        test = self._create_listening_test()
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        session_key = 'limit-test-session'
        session = self.client.session
        session.save()
        session_key = session.session_key
        for _ in range(5):
            MockAttempt.objects.create(
                test=test,
                session_key=session_key,
                is_finished=True,
                finished_at=timezone.now(),
                score_percent=50,
                correct_count=1,
                total_questions=2,
            )
        response = self.client.post(
            url,
            data=json.dumps({'action': 'save', 'answers': {}}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'limit_reached')

    def test_result_page_shows_question_type_labels(self):
        test = MockTest.objects.create(title='Result types', test_type='reading', is_active=True)
        MockQuestion.objects.create(
            test=test, order=8, part_number=1, question_type='true_false_not_given',
            question_text='Statement A', option_a='True', option_b='False', option_c='Not Given',
            correct_answer='a',
        )
        MockQuestion.objects.create(
            test=test, order=9, part_number=1, question_type='mcq',
            question_text='Pick one', option_a='A1', option_b='A2', option_c='A3', option_d='A4',
            correct_answer='b',
        )
        attempt = MockAttempt.objects.create(
            test=test,
            session_key=self.client.session.session_key or 'test-session',
            is_finished=True,
            finished_at=timezone.now(),
            answers_json={'8': 'a', '9': 'c'},
            correct_count=1,
            total_questions=2,
            score_percent=50,
        )
        self.client.get(reverse('mock_tests:test_take', kwargs={'pk': test.pk}))
        url = reverse('mock_tests:test_result', kwargs={'pk': test.pk, 'attempt_id': attempt.pk})
        html = self.client.get(url).content.decode()
        self.assertIn('mock-result-qtype', html)
        self.assertIn('True / False / Not Given', html)
        self.assertIn('tanlovli (MCQ)', html)

    def test_result_page_requires_same_session(self):
        test = self._create_listening_test()
        attempt = MockAttempt.objects.create(
            test=test,
            session_key='owner-session',
            is_finished=True,
            finished_at=timezone.now(),
            score_percent=80,
            correct_count=2,
            total_questions=3,
        )
        url = reverse('mock_tests:test_result', kwargs={'pk': test.pk, 'attempt_id': attempt.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_dock_buttons_use_ielts_numbers_when_available(self):
        from mock_tests.views import _build_blank_buttons

        test = self._create_listening_test()
        questions = list(test.questions.all())
        buttons, _ = _build_blank_buttons(questions)
        nums = [b['num'] for b in buttons]
        self.assertEqual(nums, [1, 2, 3])

        reading = MockTest.objects.create(title='Reading SC dock', test_type='reading', is_active=True)
        MockQuestion.objects.create(
            test=reading,
            order=7,
            part_number=1,
            question_type='sentence_completion',
            question_text='First [7]. Second [8]. Third [9].',
            correct_answers_json=['a', 'b', 'c'],
        )
        sc_buttons, _ = _build_blank_buttons(list(reading.questions.all()))
        self.assertEqual([b['num'] for b in sc_buttons], [7, 8, 9])

    def test_only_three_test_types(self):
        self.assertEqual(len(MockTest.TEST_TYPES), 3)
        labels = [t[0] for t in MockTest.TEST_TYPES]
        self.assertEqual(labels, ['reading', 'listening', 'writing'])

    def test_listening_question_image_on_take_page(self):
        test = self._create_listening_test()
        q = test.questions.first()
        q.image.save(
            'map.png',
            SimpleUploadedFile('map.png', b'\x89PNG\r\n\x1a\n', content_type='image/png'),
        )
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('listening-reference-figure', html)
        self.assertIn('mock-image-lightbox', html)
        self.assertEqual(html.count('mock-question-image'), 1)
        self.assertIn(q.image.url, html)

    def test_listening_block_image_shown_once_for_multiple_questions(self):
        test = self._create_listening_test()
        img = SimpleUploadedFile('map.png', b'\x89PNG\r\n\x1a\n', content_type='image/png')
        q1 = test.questions.get(order=1)
        q1.image.save('map.png', img)
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        html = self.client.get(url).content.decode()
        self.assertEqual(html.count('listening-reference-figure'), 1)

    def test_listening_summary_box_renders_in_summary_box_not_instruction(self):
        test = MockTest.objects.create(
            title='Listening Summary Box',
            test_type='listening',
            is_active=True,
        )
        MockQuestion.objects.create(
            test=test,
            order=2,
            part_number=2,
            question_type='summary_box',
            instruction='Choose the correct answers, A-I, next to questions 11-15.',
            question_text=(
                'How to use City Cycle\n\n'
                '-- Subscribe to the service online to receive a card.\n'
                '-- Select a bike by using the [11]'
            ),
            correct_answers_json=['button'],
            options_json={'word_list': ['button', 'website', 'helmet']},
        )
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        html = self.client.get(url).content.decode()
        self.assertIn('Choose the correct answers, A-I', html)
        self.assertIn('mock-summary-box', html)
        self.assertIn('How to use City Cycle', html)
        self.assertIn('mock-word-list', html)
        self.assertNotIn('listening-sa-text">How to use City Cycle', html)
        self.assertEqual(html.count('How to use City Cycle'), 1)

    def test_summary_box_hides_duplicate_instruction_when_summary_in_instruction_field(self):
        summary = (
            'How to use City Cycle\n\n'
            '-- Subscribe to the service online to receive a card.\n'
            '-- Select a bike by using the [11]'
        )
        test = MockTest.objects.create(title='Listening Summary Dup', test_type='listening', is_active=True)
        MockQuestion.objects.create(
            test=test,
            order=2,
            part_number=2,
            question_type='summary_box',
            instruction=summary,
            question_text=summary,
            correct_answers_json=['button'],
            options_json={'word_list': ['button', 'website']},
        )
        html = self.client.get(reverse('mock_tests:test_take', kwargs={'pk': test.pk})).content.decode()
        self.assertEqual(html.count('How to use City Cycle'), 1)
        self.assertNotIn('[11]', html)
        self.assertNotIn('listening-instruction-block">How to use City Cycle', html)

    def test_sanitize_block_instruction_filters_summary_text(self):
        from mock_tests.question_admin_helpers import sanitize_block_instruction

        summary = 'How to use City Cycle\n-- step [11]'
        q = MockQuestion(
            question_type='summary_box',
            instruction=summary,
            question_text=summary,
        )
        self.assertEqual(sanitize_block_instruction(summary, [q]), '')
        self.assertEqual(
            sanitize_block_instruction('Choose the correct answers, A-I.', [q]),
            'Choose the correct answers, A-I.',
        )

    def test_fix_misplaced_instruction_moves_summary_text(self):
        from mock_tests.question_admin_helpers import fix_misplaced_instruction, sync_points_from_slots

        q = MockQuestion(
            question_type='summary_box',
            instruction='How to use City Cycle\n-- step [11]',
            question_text='How to use City Cycle\n-- step [11]',
            correct_answers_json=['button'],
        )
        self.assertTrue(fix_misplaced_instruction(q))
        self.assertEqual(q.instruction, '')
        self.assertIn('[11]', q.question_text)

    def test_sync_points_from_slots_sentence_completion(self):
        from mock_tests.question_admin_helpers import sync_points_from_slots

        q = MockQuestion(
            question_type='sentence_completion',
            question_text='A [7]. B [8]. C [9].',
            correct_answers_json=['a', 'b', 'c'],
            points=1,
        )
        self.assertTrue(sync_points_from_slots(q))
        self.assertEqual(q.points, 3)

    def test_admin_form_syncs_points_on_save(self):
        from mock_tests.admin_forms import MockQuestionAdminForm

        test = MockTest.objects.create(title='Admin SC', test_type='reading', is_active=True)
        form = MockQuestionAdminForm(data={
            'test': test.pk,
            'order': 7,
            'part_number': 1,
            'question_type': 'sentence_completion',
            'question_text': 'One [7]. Two [8]. Three [9].',
            'fill_answers': 'beaks, vomiting, hardens',
            'points': 1,
        })
        self.assertTrue(form.is_valid(), form.errors)
        q = form.save()
        self.assertEqual(q.points, 3)

    def test_sentence_completion_bracket_blanks_count_and_render(self):
        test = MockTest.objects.create(title='Reading SC', test_type='reading', is_active=True)
        q = MockQuestion.objects.create(
            test=test,
            order=7,
            part_number=1,
            question_type='sentence_completion',
            instruction='Complete the sentences below with NO MORE THAN ONE WORD from the passage.',
            question_text=(
                "7 Sperm whales can't digest the beaks of the squids. [7]\n"
                "8 Sperm whales drive the irritants out by vomiting. [8]\n"
                "9 The vomit gradually hardens on contact of air. [9]"
            ),
            correct_answers_json=['beaks', 'vomiting', 'hardens'],
        )
        self.assertEqual(q.gradable_slot_count(), 3)
        self.assertTrue(q.uses_bracket_blanks())
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        html = self.client.get(url).content.decode()
        self.assertEqual(html.count('mock-sc-row'), 3)
        self.assertEqual(html.count('mock-sc-block'), 1)
        self.assertIn('mock-sc-text', html)

    def test_sentence_completion_bracket_scoring_partial(self):
        test = MockTest.objects.create(title='Reading SC score', test_type='reading', is_active=True)
        q = MockQuestion.objects.create(
            test=test,
            order=7,
            part_number=1,
            question_type='sentence_completion',
            question_text='First [7]. Second [8].',
            correct_answers_json=['beaks', 'vomiting'],
        )
        frac, got, _, _ = score_blanks(q, {'7': 'beaks', '8': 'wrong'})
        self.assertEqual(got, 1)
        self.assertAlmostEqual(frac, 0.5)

    def test_build_instruction_groups_attaches_block_image(self):
        from mock_tests.views import _build_instruction_groups

        test = self._create_listening_test()
        q = test.questions.first()
        q.image.save('m.png', SimpleUploadedFile('m.png', b'\x89PNG\r\n\x1a\n', content_type='image/png'))
        groups = _build_instruction_groups(list(test.questions.all()))
        self.assertTrue(groups)
        self.assertIsNotNone(groups[0]['image'])

    def test_admin_form_rejects_image_on_reading_test(self):
        from mock_tests.admin_forms import MockQuestionAdminForm

        reading = self._create_reading_matching_test()
        form = MockQuestionAdminForm(
            data={
                'test': reading.pk,
                'order': 5,
                'part_number': 1,
                'question_type': 'mcq',
                'question_text': 'Test?',
                'option_a': 'A',
                'option_b': 'B',
                'option_c': 'C',
                'option_d': 'D',
                'correct_answer': 'a',
                'points': 1,
            },
            files={
                'image': SimpleUploadedFile('x.png', b'\x89PNG\r\n\x1a\n', content_type='image/png'),
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)


class WritingEssayTests(TestCase):
    @classmethod
    def _create_writing_test(cls):
        test = MockTest.objects.create(
            title='Writing Demo',
            test_type='writing',
            duration_minutes=60,
            is_active=True,
        )
        q1 = MockQuestion.objects.create(
            test=test,
            order=1,
            part_number=1,
            question_type='essay',
            question_text='Task 1: Summarise the main features of the chart.',
            points=1,
        )
        q2 = MockQuestion.objects.create(
            test=test,
            order=2,
            part_number=2,
            question_type='essay',
            question_text='Task 2: Discuss both views and give your opinion.',
            points=1,
        )
        return test, q1, q2

    def test_essay_take_page_renders_textareas_and_word_count(self):
        test, q1, q2 = self._create_writing_test()
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        html = self.client.get(url).content.decode()
        self.assertEqual(html.count('mock-essay-answer'), 2)
        self.assertIn(f'name="q_{q1.pk}"', html)
        self.assertIn(f'name="q_{q2.pk}"', html)
        self.assertIn('mock-word-count', html)
        self.assertIn('mock-writing-answer-ta', html)

    def test_essay_scoring_thresholds(self):
        test, q1, _ = self._create_writing_test()
        self.assertEqual(score_extended_text('', min_words=50, target_words=250), 0.0)
        self.assertEqual(score_extended_text('x ' * 49, min_words=50, target_words=250), 0.0)
        self.assertEqual(score_extended_text('x ' * 50, min_words=50, target_words=250), 0.5)
        self.assertEqual(score_extended_text('x ' * 250, min_words=50, target_words=250), 1.0)

        short_ok, _, short_correct = check_question_answer(q1, 'too short')
        self.assertFalse(short_ok)
        self.assertIn('Writing', short_correct)

        essay = ' '.join(['word'] * 60)
        long_ok, user_disp, _ = check_question_answer(q1, essay)
        self.assertTrue(long_ok)
        self.assertTrue(len(user_disp) <= 150)
        self.assertGreater(score_question_points(q1, essay), 0.0)

    def test_essay_finish_shows_result_with_type_label(self):
        test, q1, q2 = self._create_writing_test()
        essay = ' '.join(['word'] * 60)
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        response = self.client.post(url, {
            f'q_{q1.pk}': essay,
            f'q_{q2.pk}': ' '.join(['other'] * 55),
        })
        self.assertEqual(response.status_code, 302)
        attempt = MockAttempt.objects.get(test=test, is_finished=True)
        result_url = reverse(
            'mock_tests:test_result',
            kwargs={'pk': test.pk, 'attempt_id': attempt.pk},
        )
        html = self.client.get(result_url).content.decode()
        self.assertIn('Insho', html)
        self.assertIn(essay[:80], html)


class ReadingSummaryBoxTests(TestCase):
    def test_reading_summary_box_renders_word_list_and_inline_blanks(self):
        test = MockTest.objects.create(
            title='Reading Summary Box',
            test_type='reading',
            is_active=True,
        )
        MockPassage.objects.create(test=test, order=1, title='P1', text='Sample passage about birds.')
        MockQuestion.objects.create(
            test=test,
            order=11,
            part_number=2,
            question_type='summary_box',
            instruction='Complete the summary using the list of words, A-C below.',
            question_text='Many birds migrate to [11] each winter.',
            correct_answers_json=['siberia'],
            options_json={'word_list': ['siberia', 'africa', 'europe']},
        )
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        html = self.client.get(url).content.decode()
        self.assertIn('Complete the summary using the list of words', html)
        self.assertIn('mock-summary-box', html)
        self.assertIn('mock-word-list', html)
        self.assertIn('mock-word-chip', html)
        self.assertIn('Many birds migrate to', html)
        self.assertNotIn('mock-sc-block', html)

    def test_reading_summary_box_scoring(self):
        test = MockTest.objects.create(title='Reading SB score', test_type='reading', is_active=True)
        q = MockQuestion.objects.create(
            test=test,
            order=11,
            part_number=2,
            question_type='summary_box',
            question_text='Birds fly to [11] and [12].',
            correct_answers_json=['north', 'south'],
        )
        frac, got, _, correct = score_blanks(q, {'11': 'north', '12': 'wrong'})
        self.assertEqual(got, 1)
        self.assertAlmostEqual(frac, 0.5)
        self.assertIn('north', correct)


class SummaryCompletionTests(TestCase):
    def test_summary_completion_bracket_blanks_count_and_render(self):
        test = MockTest.objects.create(title='Reading Summary Comp', test_type='reading', is_active=True)
        q = MockQuestion.objects.create(
            test=test,
            order=20,
            part_number=2,
            question_type='summary_completion',
            instruction='Complete the summary below. Choose NO MORE THAN TWO WORDS from the passage.',
            question_text=(
                '20 The research began in [20]\n'
                '21 The team focused on [21]\n'
                '22 Results were published in [22]'
            ),
            correct_answers_json=['2010', 'climate', 'spring'],
        )
        self.assertEqual(q.gradable_slot_count(), 3)
        self.assertTrue(q.uses_bracket_blanks())
        html = self.client.get(reverse('mock_tests:test_take', kwargs={'pk': test.pk})).content.decode()
        self.assertEqual(html.count('mock-sc-row'), 3)
        self.assertEqual(html.count('mock-sc-block'), 1)

    def test_summary_completion_bracket_scoring_partial(self):
        test = MockTest.objects.create(title='Summary Comp score', test_type='reading', is_active=True)
        q = MockQuestion.objects.create(
            test=test,
            order=20,
            part_number=2,
            question_type='summary_completion',
            question_text='First [20]. Second [21].',
            correct_answers_json=['alpha', 'beta'],
        )
        frac, got, _, _ = score_blanks(q, {'20': 'alpha', '21': 'wrong'})
        self.assertEqual(got, 1)
        self.assertAlmostEqual(frac, 0.5)

    def test_sync_points_from_slots_summary_completion(self):
        from mock_tests.question_admin_helpers import sync_points_from_slots

        q = MockQuestion(
            question_type='summary_completion',
            question_text='A [20]. B [21]. C [22].',
            correct_answers_json=['a', 'b', 'c'],
            points=1,
        )
        self.assertTrue(sync_points_from_slots(q))
        self.assertEqual(q.points, 3)

    def test_admin_form_syncs_points_on_save_summary_completion(self):
        from mock_tests.admin_forms import MockQuestionAdminForm

        test = MockTest.objects.create(title='Admin Summary Comp', test_type='reading', is_active=True)
        form = MockQuestionAdminForm(data={
            'test': test.pk,
            'order': 20,
            'part_number': 2,
            'question_type': 'summary_completion',
            'question_text': 'One [20]. Two [21]. Three [22].',
            'fill_answers': 'alpha, beta, gamma',
            'points': 1,
        })
        self.assertTrue(form.is_valid(), form.errors)
        q = form.save()
        self.assertEqual(q.points, 3)


class AdminEstimateSlotsTests(TestCase):
    def test_estimate_gradable_slots_matches_js_logic(self):
        from mock_tests.question_admin_helpers import estimate_gradable_slots

        self.assertEqual(
            estimate_gradable_slots('sentence_completion', question_text='A [7]. B [8]. C [9].'),
            3,
        )
        self.assertEqual(
            estimate_gradable_slots('summary_completion', question_text='A [20]. B [21].'),
            2,
        )
        self.assertEqual(
            estimate_gradable_slots('summary_box', fill_answers='a, b, c'),
            3,
        )
        self.assertEqual(
            estimate_gradable_slots(
                'matching_headings',
                matching_correct='14:i\n15:ii',
            ),
            2,
        )
        self.assertEqual(estimate_gradable_slots('mcq'), 1)

    def test_fix_mock_questions_command_syncs_points(self):
        from io import StringIO

        from django.core.management import call_command

        test = MockTest.objects.create(title='Fix Cmd', test_type='reading', is_active=True)
        q = MockQuestion.objects.create(
            test=test,
            order=7,
            part_number=1,
            question_type='summary_completion',
            question_text='One [7]. Two [8]. Three [9].',
            correct_answers_json=['a', 'b', 'c'],
            points=1,
        )
        out = StringIO()
        call_command('fix_mock_questions', stdout=out)
        q.refresh_from_db()
        self.assertEqual(q.points, 3)
        self.assertIn('Ball: 1 ta tuzatildi', out.getvalue())


class McqExtendedTests(TestCase):
    def test_mcq_eight_options(self):
        test = MockTest.objects.create(title='MCQ 8', test_type='reading', is_active=True)
        q = MockQuestion.objects.create(
            test=test, order=1, question_type='mcq',
            question_text='Pick one',
            option_a='A', option_b='B', option_c='C', option_d='D',
            option_e='E', option_f='F', option_g='G', option_h='H',
            correct_answer='h',
        )
        self.assertEqual(len(q.get_mcq_options()), 8)

    def test_mcq_two_answers_scoring(self):
        test = MockTest.objects.create(title='MCQ multi', test_type='reading', is_active=True)
        q = MockQuestion.objects.create(
            test=test, order=1, question_type='mcq', mcq_select_count=2,
            question_text='Choose two',
            option_a='A', option_b='B', option_c='C', option_d='D',
            correct_answer='a,c',
        )
        from mock_tests.mcq_utils import score_mcq
        frac_ok, ok, _, _ = score_mcq(q, 'a,c')
        self.assertTrue(ok)
        self.assertEqual(frac_ok, 1.0)
        frac_bad, ok_bad, _, _ = score_mcq(q, 'a,b')
        self.assertFalse(ok_bad)

    def test_mcq_multi_renders_checkboxes(self):
        test = MockTest.objects.create(title='MCQ UI', test_type='reading', is_active=True)
        MockQuestion.objects.create(
            test=test, order=1, question_type='mcq', mcq_select_count=2,
            question_text='Choose two',
            option_a='A', option_b='B', option_c='C', option_d='D',
            correct_answer='a,b',
        )
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        html = Client().get(url).content.decode()
        self.assertIn('mock-mcq-check', html)
        self.assertIn('2 ta javob tanlang', html)

    def test_mcq_admin_validates_answer_count(self):
        from mock_tests.admin_forms import MockQuestionAdminForm
        test = MockTest.objects.create(title='T', test_type='reading', is_active=True)
        form = MockQuestionAdminForm(data={
            'test': test.pk, 'order': 1, 'part_number': 1,
            'question_type': 'mcq', 'mcq_select_count': 2,
            'question_text': 'Q?', 'option_a': 'A', 'option_b': 'B', 'option_c': 'C',
            'correct_answer': 'a', 'points': 1,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('correct_answer', form.errors)


class StatsTests(MockTestFixturesMixin, TestCase):
    def test_dashboard_stats_counts_sessions(self):
        test = self._create_listening_test()
        MockAttempt.objects.create(
            test=test, session_key='sess-a', is_finished=True,
            score_percent=80, correct_count=1, total_questions=2,
            finished_at=timezone.now(),
        )
        MockAttempt.objects.create(
            test=test, session_key='sess-a', is_finished=False,
        )
        MockAttempt.objects.create(
            test=test, session_key='sess-b', is_finished=True,
            score_percent=50, correct_count=1, total_questions=2,
            finished_at=timezone.now(),
        )
        stats = get_dashboard_stats()
        self.assertEqual(stats['unique_sessions'], 2)
        self.assertEqual(stats['finished_attempts'], 2)
        self.assertEqual(stats['in_progress'], 1)
        self.assertEqual(stats['total_attempts'], 3)
