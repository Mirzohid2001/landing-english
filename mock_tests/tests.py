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

    def test_reading_dock_sequential_across_parts(self):
        from mock_tests.views import _build_part_groups

        test = MockTest.objects.create(title='Reading 40', test_type='reading', is_active=True)
        for i in range(1, 10):
            MockQuestion.objects.create(
                test=test,
                order=10 + i,
                part_number=3,
                question_type='true_false_not_given',
                question_text=f'Statement {i}',
                option_a='True',
                option_b='False',
                option_c='Not Given',
                correct_answer='a',
            )
        MockQuestion.objects.create(
            test=test,
            order=19,
            part_number=3,
            question_type='summary_box',
            question_text='Text [36] and [37] and [38] and [39] and [40].',
            correct_answers_json=['a', 'b', 'c', 'd', 'e'],
            options_json={'word_list': ['a', 'b', 'c', 'd', 'e', 'f']},
        )
        for i in range(1, 14):
            MockQuestion.objects.create(
                test=test,
                order=i,
                part_number=1,
                question_type='true_false_not_given',
                question_text=f'P1 {i}',
                option_a='True',
                option_b='False',
                option_c='Not Given',
                correct_answer='a',
            )
        for i in range(1, 14):
            MockQuestion.objects.create(
                test=test,
                order=13 + i,
                part_number=2,
                question_type='true_false_not_given',
                question_text=f'P2 {i}',
                option_a='True',
                option_b='False',
                option_c='Not Given',
                correct_answer='a',
            )
        questions = list(test.questions.all())
        groups = _build_part_groups(test, questions, [])
        all_nums = []
        for g in groups:
            all_nums.extend(b['num'] for b in g['blank_buttons'])
        self.assertEqual(all_nums, list(range(1, 41)))
        part3 = next(g for g in groups if g['part_number'] == 3)
        self.assertEqual([b['num'] for b in part3['blank_buttons']], list(range(27, 41)))

    def test_reading_ui_labels_follow_dock_sequence(self):
        test = MockTest.objects.create(title='UI labels', test_type='reading', is_active=True)
        MockQuestion.objects.create(
            test=test, order=1, part_number=1, question_type='matching_features',
            question_text='Match features',
            options_json={
                'items': [
                    {'num': 1, 'label': 'one'}, {'num': 2, 'label': 'two'},
                    {'num': 3, 'label': 'three'}, {'num': 4, 'label': 'four'},
                    {'num': 5, 'label': 'five'}, {'num': 6, 'label': 'six'},
                ],
                'options': [{'letter': 'a', 'text': 'A'}],
            },
            correct_answers_json={str(i): 'a' for i in range(1, 7)},
        )
        MockQuestion.objects.create(
            test=test, order=2, part_number=1, question_type='sentence_completion',
            question_text='First [7]. Second [8]. Third [9].',
            correct_answers_json=['a', 'b', 'c'],
        )
        for i in range(3, 7):
            MockQuestion.objects.create(
                test=test, order=i, part_number=1, question_type='true_false_not_given',
                question_text=f'Statement {i}', option_a='T', option_b='F', option_c='NG',
                correct_answer='a',
            )
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('aria-hidden="true">7</span>', html)
        self.assertIn('aria-hidden="true">8</span>', html)
        self.assertIn('aria-hidden="true">9</span>', html)
        self.assertIn('class="mock-q-num-box">10</span>', html)

    def test_reading_scoring_dock_matches_part_dock_with_overlapping_orders(self):
        from mock_tests.views import _build_part_groups
        from mock_tests.services.scoring import _dock_buttons_by_question

        test = MockTest.objects.create(title='Dock align', test_type='reading', is_active=True)
        for i in range(1, 14):
            MockQuestion.objects.create(
                test=test, order=i, part_number=1, question_type='true_false_not_given',
                question_text=f'P1 {i}', option_a='T', option_b='F', option_c='NG', correct_answer='a',
            )
        for i in range(1, 14):
            MockQuestion.objects.create(
                test=test, order=13 + i, part_number=2, question_type='true_false_not_given',
                question_text=f'P2 {i}', option_a='T', option_b='F', option_c='NG', correct_answer='a',
            )
        for i in range(10, 15):
            MockQuestion.objects.create(
                test=test, order=i, part_number=3, question_type='true_false_not_given',
                question_text=f'P3 {i}', option_a='T', option_b='F', option_c='NG', correct_answer='a',
            )
        MockQuestion.objects.create(
            test=test, order=19, part_number=3, question_type='summary_box',
            question_text='A [36] B [37] C [38] D [39] E [40].',
            correct_answers_json=['a', 'b', 'c', 'd', 'e'],
            options_json={'word_list': ['a', 'b', 'c', 'd', 'e', 'f']},
        )
        questions = list(test.questions.all())
        groups = _build_part_groups(test, questions, [])
        ui_nums = {(b['question_id'], b.get('blank_key', '')): b['num']
                   for g in groups for b in g['blank_buttons']}
        score_nums = {(b['question_id'], b.get('blank_key', '')): b['num']
                      for bs in _dock_buttons_by_question(questions).values() for b in bs}
        self.assertEqual(ui_nums, score_nums)

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
        sc_buttons, _ = _build_blank_buttons(
            list(reading.questions.all()), sequential_only=True,
        )
        self.assertEqual([b['num'] for b in sc_buttons], [1, 2, 3])

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
        self.assertIn('mock-word-bank', html)
        self.assertIn('mock-summary-select', html)
        self.assertIn('mock-summary-line', html)
        self.assertIn('mock-summary-num', html)
        self.assertIn('How to use City Cycle', html)
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

    def test_fill_blank_bracket_scoring_and_result_rows(self):
        test = MockTest.objects.create(title='Fill multi', test_type='reading', is_active=True)
        q = MockQuestion.objects.create(
            test=test,
            order=3,
            part_number=1,
            question_type='fill_blank',
            question_text='Item [16] then [17] then [18] then [19] then [20].',
            correct_answers_json=['e', 'f', 'a', 'h', 'b'],
            points=5,
        )
        self.assertEqual(q.gradable_slot_count(), 5)
        self.assertTrue(q.uses_bracket_blanks())

        frac, got, user_disp, correct_disp = score_blanks(q, {'16': 'e', '17': 'a', '18': '', '19': '', '20': ''})
        self.assertEqual(got, 1)
        self.assertAlmostEqual(frac, 0.2)

        attempt = MockAttempt.objects.create(
            test=test,
            session_key='fill-multi',
            answers_json={str(q.pk): {'16': 'e', '17': 'a', '18': '', '19': '', '20': ''}},
            is_finished=True,
            correct_count=1,
            total_questions=5,
            score_percent=20,
        )
        result = score_attempt(attempt, [q])
        self.assertEqual(len(result['details']), 5)
        self.assertEqual(result['details'][0]['user_answer_display'], 'e')
        self.assertEqual(result['details'][0]['correct_answer'], 'e')
        self.assertNotIn("{'16'", str(result['details']))

        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        html = self.client.get(url).content.decode()
        self.assertEqual(html.count('mock-sc-row'), 5)

    def test_reading_completion_block_layout(self):
        test = MockTest.objects.create(title='Completion layout', test_type='reading', is_active=True)
        for i in range(1, 14):
            MockQuestion.objects.create(
                test=test, order=i, part_number=1,
                question_type='true_false_not_given',
                question_text=f'Q {i}', option_a='T', option_b='F', option_c='NG',
                correct_answer='a',
            )
        for i in range(14, 24):
            MockQuestion.objects.create(
                test=test, order=i, part_number=2,
                question_type='true_false_not_given',
                question_text=f'Q {i}', option_a='T', option_b='F', option_c='NG',
                correct_answer='a',
            )
        MockQuestion.objects.create(
            test=test,
            order=24,
            part_number=2,
            question_type='sentence_completion',
            instruction='Choose ONE WORD ONLY from the passage for each answer',
            question_text=(
                'Celebrities achieve a global status\n\n'
                'The development of publishing meant readers learned about celebrities by reading [24]. '
                'Mass media meant a person\'s [25] rather than talent could bring fame. '
                'Fame may depend on the response of the [26].'
            ),
            correct_answers_json=['newspapers', 'personality', 'public'],
        )
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        html = self.client.get(url).content.decode()
        self.assertIn('mock-completion-range', html)
        self.assertIn('Questions 24-26', html)
        self.assertIn('mock-completion-title', html)
        self.assertIn('Celebrities achieve a global status', html)
        self.assertIn('mock-completion-panel', html)
        self.assertIn('mock-completion-input', html)

    def test_reading_sentence_completion_inline_matches_dock_not_brackets(self):
        test = MockTest.objects.create(title='Reading SC inline', test_type='reading', is_active=True)
        for i in range(1, 14):
            MockQuestion.objects.create(
                test=test, order=i, part_number=1, question_type='true_false_not_given',
                question_text=f'P1 {i}', option_a='T', option_b='F', option_c='NG', correct_answer='a',
            )
        for i in range(1, 9):
            MockQuestion.objects.create(
                test=test, order=i, part_number=2, question_type='true_false_not_given',
                question_text=f'P2 {i}', option_a='T', option_b='F', option_c='NG', correct_answer='a',
            )
        MockQuestion.objects.create(
            test=test,
            order=9,
            part_number=2,
            question_type='sentence_completion',
            instruction='Choose ONE WORD ONLY from the passage for each answer',
            question_text=(
                'The development of publishing meant readers learned about celebrities by reading [24]. '
                'Mass media meant a person\'s [25] rather than talent could bring fame. '
                'Fame may depend on the response of the [26].'
            ),
            correct_answers_json=['newspapers', 'personality', 'public'],
        )
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        html = self.client.get(url).content.decode()
        self.assertIn('mock-reading-inline', html)
        self.assertNotIn('mock-sc-row', html)
        self.assertIn('aria-hidden="true">22</span>', html)
        self.assertIn('aria-hidden="true">23</span>', html)
        self.assertIn('aria-hidden="true">24</span>', html)
        self.assertNotIn('aria-hidden="true">25</span>', html)

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
        self.assertEqual(html.count('mock-reading-inline-blank'), 3)
        self.assertIn('mock-reading-inline-text', html)

    def test_sentence_completion_multiline_underscore_before_bracket(self):
        test = MockTest.objects.create(title='Reading SC multiline', test_type='reading', is_active=True)
        q = MockQuestion.objects.create(
            test=test,
            order=2,
            part_number=1,
            question_type='sentence_completion',
            instruction='Complete the sentences below with NO MORE THAN ONE WORD from the passage.',
            question_text=(
                "7 Sperm whales can't digest the\n"
                "________ of the squids.\n"
                "[7]\n"
                "\n"
                "8 Sperm whales drive the irritants out of\n"
                "their intestines by ________.\n"
                "[8]"
            ),
            correct_answers_json=['beaks', 'vomiting'],
        )
        rows = q.get_bracket_completion_rows()
        self.assertEqual(len(rows), 2)
        self.assertIn('Sperm whales', rows[0]['before'])
        self.assertIn('squids', rows[0]['after'])
        html = self.client.get(reverse('mock_tests:test_take', kwargs={'pk': test.pk})).content.decode()
        self.assertIn('Sperm whales', html)
        self.assertIn('digest the', html)
        self.assertIn('of the squids', html)

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
        self.assertIn('mock-word-bank', html)
        self.assertIn('mock-summary-select', html)
        self.assertIn('mock-summary-line', html)
        self.assertIn('Many birds migrate to', html)
        self.assertNotIn('mock-sc-block', html)

    def test_summary_box_lines_keep_blanks_inline(self):
        test = MockTest.objects.create(title='SB inline', test_type='listening', is_active=True)
        q = MockQuestion.objects.create(
            test=test,
            order=1,
            question_type='summary_box',
            question_text=(
                'How to use City Cycle\n'
                '-- Select a bike by using the [11]\n'
                '-- Release the bike by using the [12] of your chosen bike.'
            ),
            correct_answers_json=['a', 'b'],
            options_json={'word_list': ['button', 'website']},
        )
        lines = q.get_summary_lines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0]['is_title'])
        line_with_blank = lines[1]['segments']
        types = [s['type'] for s in line_with_blank]
        self.assertEqual(types, ['text', 'blank'])
        self.assertIn('using the ', line_with_blank[0]['value'])
        html = self.client.get(reverse('mock_tests:test_take', kwargs={'pk': test.pk})).content.decode()
        self.assertIn('mock-summary-num', html)
        self.assertIn('mock-summary-line--title', html)

    def test_reading_tfng_renders_three_options(self):
        test = MockTest.objects.create(title='Reading TFNG', test_type='reading', is_active=True)
        MockQuestion.objects.create(
            test=test,
            order=3,
            part_number=1,
            question_type='true_false_not_given',
            question_text='The statement agrees with the passage.',
            option_a='True',
            option_b='False',
            option_c='Not Given',
            correct_answer='b',
        )
        html = self.client.get(reverse('mock_tests:test_take', kwargs={'pk': test.pk})).content.decode()
        self.assertEqual(html.count('mock-option--inline'), 3)
        self.assertIn('NOT GIVEN', html)
        self.assertIn('mock-q-row--choice', html)

    def test_reading_summary_box_matches_listening_layout(self):
        test = MockTest.objects.create(title='Reading SB layout', test_type='reading', is_active=True)
        MockQuestion.objects.create(
            test=test,
            order=11,
            part_number=2,
            question_type='summary_box',
            instruction='Choose words from the box.',
            question_text='Birds fly to [11] each winter.',
            correct_answers_json=['siberia'],
            options_json={'word_list': ['siberia', 'africa', 'europe']},
        )
        html = self.client.get(reverse('mock_tests:test_take', kwargs={'pk': test.pk})).content.decode()
        self.assertIn('mock-q-card--summary-box', html)
        self.assertIn('mock-summary-line', html)
        self.assertIn('mock-word-bank-title', html)
        self.assertIn('Variants', html)

    def test_reading_summary_box_scoring(self):
        test = MockTest.objects.create(title='Reading SB score', test_type='reading', is_active=True)
        q = MockQuestion.objects.create(
            test=test,
            order=11,
            part_number=2,
            question_type='summary_box',
            question_text='Birds fly to [11] and [12].',
            correct_answers_json=['north', 'south'],
            options_json={'word_list': ['north', 'south', 'east']},
        )
        frac, got, _, correct = score_blanks(q, {'11': 'north', '12': 'wrong'})
        self.assertEqual(got, 1)
        self.assertAlmostEqual(frac, 0.5)
        self.assertIn('a', correct)

        frac_letters, got_letters, _, _ = score_blanks(q, {'11': 'a', '12': 'b'})
        self.assertEqual(got_letters, 2)
        self.assertAlmostEqual(frac_letters, 1.0)


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
        self.assertEqual(html.count('mock-reading-inline-blank'), 3)
        self.assertIn('mock-reading-inline-text', html)

    def test_summary_completion_multiline_underscore_before_bracket(self):
        test = MockTest.objects.create(title='Summary multiline', test_type='reading', is_active=True)
        MockQuestion.objects.create(
            test=test,
            order=2,
            part_number=1,
            question_type='summary_completion',
            question_text=(
                "7 Whales eat squid but cannot digest\n"
                "________ inside their stomachs.\n"
                "[7]"
            ),
            correct_answers_json=['beaks'],
        )
        html = self.client.get(reverse('mock_tests:test_take', kwargs={'pk': test.pk})).content.decode()
        self.assertIn('Whales eat squid', html)
        self.assertIn('inside their stomachs', html)

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


class SlotAlignmentTests(TestCase):
    def test_summary_box_slots_follow_brackets_not_answer_count(self):
        from mock_tests.services.slots import list_gradable_slots
        from mock_tests.views import _build_blank_buttons

        test = MockTest.objects.create(title='SB slots', test_type='reading', is_active=True)
        q = MockQuestion.objects.create(
            test=test,
            order=1,
            question_type='summary_box',
            question_text='Birds fly to [11] only.',
            correct_answers_json=['north', 'south', 'east'],
        )
        slots = list_gradable_slots(q)
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0].key, '11')
        self.assertEqual(q.gradable_slot_count(), 1)
        buttons, _ = _build_blank_buttons([q], sequential_only=True)
        self.assertEqual([b['num'] for b in buttons], [1])
        self.assertEqual(len(buttons), 1)

    def test_fill_blank_variants_are_single_slot(self):
        test = MockTest.objects.create(title='Fill variants', test_type='listening', is_active=True)
        q = MockQuestion.objects.create(
            test=test,
            order=2,
            question_type='fill_blank',
            question_text='Starts at ______',
            correct_answers_json=['9', 'nine'],
        )
        self.assertEqual(q.gradable_slot_count(), 1)

    def test_matching_slots_follow_ui_fields(self):
        from mock_tests.services.slots import list_gradable_slots
        from mock_tests.views import _build_blank_buttons

        test = MockTestFixturesMixin._create_reading_matching_test()
        q = test.questions.get(question_type='matching_headings')
        slots = list_gradable_slots(q)
        self.assertEqual(len(slots), 2)
        buttons, _ = _build_blank_buttons([q])
        self.assertEqual(len(buttons), 2)
        self.assertEqual({b['blank_key'] for b in buttons}, {'14', '15'})

    def test_dock_matches_result_rows_for_sentence_completion(self):
        from mock_tests.views import _build_blank_buttons
        from mock_tests.services.scoring import expand_question_details

        test = MockTest.objects.create(title='Align SC', test_type='reading', is_active=True)
        q = MockQuestion.objects.create(
            test=test,
            order=7,
            question_type='sentence_completion',
            question_text='One [7]. Two [8]. Three [9].',
            correct_answers_json=['a', 'b', 'c'],
        )
        buttons, _ = _build_blank_buttons([q])
        rows = expand_question_details(q, {'7': 'a', '8': 'x', '9': 'c'})
        self.assertEqual(len(buttons), len(rows))
        self.assertEqual(q.gradable_slot_count(), 3)


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
            estimate_gradable_slots('summary_box', question_text='A [11]. B [12]. C [13].'),
            3,
        )
        self.assertEqual(
            estimate_gradable_slots('summary_box', fill_answers='a, b, c'),
            1,
        )
        self.assertEqual(
            estimate_gradable_slots(
                'matching_headings',
                matching_correct='14:i\n15:ii',
            ),
            2,
        )
        self.assertEqual(
            estimate_gradable_slots('fill_blank', question_text='A [16]. B [17].'),
            2,
        )
        self.assertEqual(estimate_gradable_slots('mcq', mcq_select_count=2), 2)
        self.assertEqual(estimate_gradable_slots('mcq', mcq_select_count=3), 3)

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
        frac_ok, ok, _, correct_disp = score_mcq(q, 'a,c')
        self.assertTrue(ok)
        self.assertEqual(frac_ok, 1.0)
        self.assertEqual(correct_disp, 'a,c')

        frac_partial, ok_partial, user_disp, _ = score_mcq(q, 'a,d')
        self.assertFalse(ok_partial)
        self.assertEqual(frac_partial, 0.5)
        self.assertEqual(user_disp, 'a,d')

        frac_one, ok_one, _, _ = score_mcq(q, 'a,b')
        self.assertFalse(ok_one)
        self.assertEqual(frac_one, 0.5)

    def test_mcq_two_answers_result_rows(self):
        from mock_tests.services.scoring import expand_question_details, score_attempt
        from mock_tests.models import MockAttempt

        test = MockTest.objects.create(title='MCQ result', test_type='reading', is_active=True)
        q = MockQuestion.objects.create(
            test=test, order=5, question_type='mcq', mcq_select_count=2,
            question_text='Choose two',
            option_a='A', option_b='B', option_c='C', option_d='D',
            correct_answer='a,c', points=2,
        )
        rows = expand_question_details(q, 'a,d')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['order'], 5)
        self.assertEqual(rows[1]['order'], 6)
        self.assertEqual(rows[0]['label'], 'Savol 5 — [5]')
        self.assertEqual(rows[1]['label'], 'Savol 5 — [6]')
        self.assertTrue(rows[0]['is_correct'])
        self.assertEqual(rows[0]['correct_answer'], 'a')
        self.assertFalse(rows[1]['is_correct'])
        self.assertEqual(rows[1]['correct_answer'], 'c')
        self.assertEqual(rows[1]['user_answer_display'], 'd')

        attempt = MockAttempt.objects.create(
            test=test, session_key='mcq-res', answers_json={str(q.id): 'a,d'}, is_finished=True,
        )
        result = score_attempt(attempt, [q])
        self.assertEqual(result['earned_points'], 1.0)
        detail_rows = [d for d in result['details'] if d['question_id'] == q.id]
        self.assertEqual(len(detail_rows), 2)
        self.assertTrue(any(d['correct_answer'] == 'c' for d in detail_rows))

    def test_mcq_two_answers_labels_follow_dock_after_notes(self):
        from mock_tests.services.scoring import _dock_buttons_by_question, expand_question_details, score_attempt

        test = MockTest.objects.create(title='MCQ dock labels', test_type='listening', is_active=True)
        notes = MockQuestion.objects.create(
            test=test,
            order=4,
            question_type='notes_completion',
            question_text='Effect [23]',
            correct_answers_json=['explode'],
        )
        mcq = MockQuestion.objects.create(
            test=test,
            order=5,
            question_type='mcq',
            mcq_select_count=2,
            question_text='Choose TWO',
            option_a='A', option_b='B', option_c='C', option_d='D', option_e='E',
            correct_answer='a,e',
            points=2,
        )
        dock = _dock_buttons_by_question([notes, mcq])
        rows = expand_question_details(mcq, '', dock)
        self.assertEqual(rows[0]['label'], 'Savol 5 — [24]')
        self.assertEqual(rows[1]['label'], 'Savol 5 — [25]')
        self.assertEqual(rows[0]['order'], 24)
        self.assertEqual(rows[1]['order'], 25)

        attempt = MockAttempt.objects.create(
            test=test,
            session_key='mcq-dock-lbl',
            answers_json={str(notes.pk): {'23': ''}, str(mcq.pk): ''},
            is_finished=True,
        )
        result = score_attempt(attempt, [notes, mcq])
        mcq_labels = [d['label'] for d in result['details'] if d['question_id'] == mcq.id]
        self.assertEqual(mcq_labels, ['Savol 5 — [24]', 'Savol 5 — [25]'])

    def test_result_labels_consistent_across_question_types(self):
        from mock_tests.services.scoring import score_attempt

        test = MockTest.objects.create(title='Label mix', test_type='listening', is_active=True)
        notes = MockQuestion.objects.create(
            test=test,
            order=4,
            part_number=1,
            question_type='notes_completion',
            question_text='Effect [23]',
            correct_answers_json=['explode'],
        )
        mcq = MockQuestion.objects.create(
            test=test,
            order=5,
            part_number=1,
            question_type='mcq',
            question_text='Choose one',
            option_a='A', option_b='B', option_c='C', option_d='D',
            correct_answer='a',
        )
        attempt = MockAttempt.objects.create(
            test=test,
            session_key='label-mix',
            answers_json={str(notes.pk): {'23': ''}, str(mcq.pk): 'a'},
            is_finished=True,
        )
        result = score_attempt(attempt, [notes, mcq])
        labels = [d['label'] for d in result['details']]
        self.assertEqual(labels[0], 'Savol 4 — [23]')
        self.assertEqual(labels[1], 'Savol 5 — [24]')

    def test_mcq_multi_renders_checkboxes(self):
        test = MockTest.objects.create(title='MCQ UI', test_type='reading', is_active=True)
        MockQuestion.objects.create(
            test=test, order=24, question_type='mcq', mcq_select_count=2,
            question_text='Choose two',
            option_a='A', option_b='B', option_c='C', option_d='D',
            correct_answer='a,b',
        )
        url = reverse('mock_tests:test_take', kwargs={'pk': test.pk})
        html = Client().get(url).content.decode()
        self.assertIn('mock-mcq-check', html)
        self.assertIn('2 ta javob tanlang', html)
        self.assertIn('mock-q-num-box--range', html)
        self.assertIn('1-2', html)

    def test_mcq_multi_order_display_and_dock(self):
        from mock_tests.views import _build_blank_buttons

        test = MockTest.objects.create(title='MCQ dock', test_type='listening', is_active=True)
        q = MockQuestion.objects.create(
            test=test, order=24, part_number=1, question_type='mcq', mcq_select_count=2,
            question_text='Choose TWO', option_a='A', option_b='B', option_c='C',
            correct_answer='a,c',
        )
        self.assertEqual(q.get_order_display_label(), '24-25')
        self.assertEqual(q.gradable_slot_count(), 2)
        buttons, _ = _build_blank_buttons([q])
        self.assertEqual([b['num'] for b in buttons], [24, 25])

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

    def test_tfng_admin_form_accepts_three_options(self):
        from mock_tests.admin_forms import MockQuestionAdminForm

        test = MockTest.objects.create(title='TFNG', test_type='reading', is_active=True)
        form = MockQuestionAdminForm(data={
            'test': test.pk,
            'order': 3,
            'part_number': 1,
            'question_type': 'true_false_not_given',
            'question_text': 'The statement agrees with the passage.',
            'option_a': 'True',
            'option_b': 'False',
            'option_c': 'Not Given',
            'correct_answer': 'c',
            'points': 1,
        })
        self.assertTrue(form.is_valid(), form.errors)
        q = form.save()
        self.assertEqual(len(q.get_tfng_options()), 3)
        self.assertEqual(q.get_tfng_options()[2]['text'], 'Not Given')


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


class AdminFillValidationTests(TestCase):
    def _base_form_data(self, test, **overrides):
        data = {
            'test': test.pk,
            'order': 3,
            'part_number': 1,
            'question_type': 'fill_blank',
            'points': 1,
        }
        data.update(overrides)
        return data

    def test_fill_blank_bracket_count_must_match_answers(self):
        from mock_tests.admin_forms import MockQuestionAdminForm

        test = MockTest.objects.create(title='Admin FB brackets', test_type='reading', is_active=True)
        form = MockQuestionAdminForm(data=self._base_form_data(
            test,
            question_text='Item [16] then [17] then [18].',
            fill_answers='e, f',
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('fill_answers', form.errors)

    def test_fill_blank_comma_variants_without_brackets_valid(self):
        from mock_tests.admin_forms import MockQuestionAdminForm

        test = MockTest.objects.create(title='Admin FB variants', test_type='listening', is_active=True)
        form = MockQuestionAdminForm(data=self._base_form_data(
            test,
            question_text='Starts at ______',
            fill_answers='9, nine',
        ))
        self.assertTrue(form.is_valid(), form.errors)
        q = form.save()
        self.assertEqual(q.correct_answers_json, ['9', 'nine'])
        self.assertEqual(q.gradable_slot_count(), 1)

    def test_fill_blank_rejects_answers_without_question_text(self):
        from mock_tests.admin_forms import MockQuestionAdminForm

        test = MockTest.objects.create(title='Admin FB empty text', test_type='reading', is_active=True)
        form = MockQuestionAdminForm(data=self._base_form_data(
            test,
            question_text='',
            fill_answers='answer',
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('question_text', form.errors)

    def test_fill_blank_requires_answers_when_question_text_present(self):
        from mock_tests.admin_forms import MockQuestionAdminForm

        test = MockTest.objects.create(title='Admin FB no answers', test_type='reading', is_active=True)
        form = MockQuestionAdminForm(data=self._base_form_data(
            test,
            question_text='The answer is ______',
            fill_answers='',
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('fill_answers', form.errors)

    def test_summary_box_requires_brackets_in_question_text(self):
        from mock_tests.admin_forms import MockQuestionAdminForm

        test = MockTest.objects.create(title='Admin SB', test_type='reading', is_active=True)
        form = MockQuestionAdminForm(data={
            'test': test.pk,
            'order': 1,
            'part_number': 1,
            'question_type': 'summary_box',
            'question_text': 'No brackets here.',
            'fill_answers': 'north',
            'word_list_lines': 'north\nsouth',
            'points': 1,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('question_text', form.errors)

    def test_validate_fill_helpers_parse_and_brackets(self):
        from mock_tests.question_admin_helpers import (
            find_bracket_numbers,
            parse_fill_answers,
            validate_fill_type_fields,
        )

        self.assertEqual(parse_fill_answers('9, nine'), ['9', 'nine'])
        self.assertEqual(find_bracket_numbers('A [7]. B [8].'), ['7', '8'])
        errors = validate_fill_type_fields(
            'fill_blank',
            question_text='One [1]. Two [2].',
            fill_answers='only',
        )
        self.assertIn('fill_answers', errors)
        self.assertEqual(
            validate_fill_type_fields(
                'fill_blank',
                question_text='Starts at ______',
                fill_answers='9, nine',
            ),
            {},
        )


class ReadingParserBlankLineTests(TestCase):
    """Bo'sh qator — blok chegarasi; intro `instruction` maydonida bo'lishi kerak."""

    def test_blank_line_stops_backward_scan_intro_not_in_row(self):
        test = MockTest.objects.create(title='Reading blank line', test_type='reading', is_active=True)
        q = MockQuestion.objects.create(
            test=test,
            order=7,
            part_number=1,
            question_type='sentence_completion',
            instruction='Complete the sentences below with NO MORE THAN ONE WORD from the passage.',
            question_text=(
                'The sperm whale is a large mammal.\n'
                '\n'
                "7 Sperm whales can't digest the\n"
                '________ of the squids.\n'
                '[7]\n'
                '\n'
                '8 Sperm whales drive the irritants out of\n'
                'their intestines by ________.\n'
                '[8]'
            ),
            correct_answers_json=['beaks', 'vomiting'],
        )
        rows = q.get_bracket_completion_rows()
        self.assertEqual(len(rows), 2)
        self.assertNotIn('large mammal', rows[0]['before'])
        self.assertIn('Sperm whales', rows[0]['before'])
        self.assertIn('squids', rows[0]['after'])
        self.assertNotIn('large mammal', rows[1]['before'])
        self.assertIn('irritants', rows[1]['before'])

    def test_take_page_shows_instruction_not_question_text_intro(self):
        test = MockTest.objects.create(title='Reading intro render', test_type='reading', is_active=True)
        MockQuestion.objects.create(
            test=test,
            order=7,
            part_number=1,
            question_type='sentence_completion',
            instruction='Background context for questions 7-8.',
            question_text=(
                "7 Sperm whales can't digest the\n"
                '________ of the squids.\n'
                '[7]'
            ),
            correct_answers_json=['beaks'],
        )
        html = self.client.get(reverse('mock_tests:test_take', kwargs={'pk': test.pk})).content.decode()
        self.assertIn('Background context', html)
        self.assertIn('digest the', html)
