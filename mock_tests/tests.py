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
from mock_tests.services.scoring import check_question_answer, score_attempt
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
        self.assertEqual(result['earned_points'], 0.5)
        self.assertFalse(result['details'][0]['is_correct'])

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
    def test_bracket_segments(self):
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
