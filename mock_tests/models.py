import re

from django.db import models
from django.urls import reverse

from .matching_utils import (
    MATCHING_TYPES,
    build_matching_fields,
    get_matching_ref_options,
    is_matching_type,
    is_multi_matching_type,
    matching_ref_title,
)


class MockTest(models.Model):
    TEST_TYPES = [
        ('reading', 'Reading'),
        ('listening', 'Listening'),
        ('writing', 'Writing'),
    ]
    DIFFICULTY_LEVELS = [
        ('easy', 'Oson'),
        ('medium', "O'rta"),
        ('hard', 'Qiyin'),
    ]

    title = models.CharField(max_length=300, verbose_name='Sarlavha')
    test_type = models.CharField(max_length=20, choices=TEST_TYPES, verbose_name='Test turi')
    difficulty = models.CharField(
        max_length=10, choices=DIFFICULTY_LEVELS, default='medium', verbose_name='Qiyinlik'
    )
    description = models.TextField(blank=True, verbose_name='Tavsif')
    duration_minutes = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Davomiyligi (daqiqa)'
    )
    passing_score = models.PositiveIntegerField(default=60, verbose_name="O'tish balli (%)")
    audio_file = models.FileField(
        upload_to='mock_tests/audio/', blank=True, null=True, verbose_name='Audio (Listening)'
    )
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Demo test'
        verbose_name_plural = 'Demo testlar'

    def __str__(self):
        return f'{self.title} ({self.get_test_type_display()})'

    @property
    def total_questions(self):
        return self.questions.count()

    def get_absolute_url(self):
        return reverse('mock_tests:test_detail', kwargs={'pk': self.pk})


class MockPassage(models.Model):
    test = models.ForeignKey(
        MockTest, on_delete=models.CASCADE, related_name='passages', verbose_name='Test'
    )
    order = models.PositiveSmallIntegerField(default=1, verbose_name='Tartib')
    title = models.CharField(max_length=300, blank=True, verbose_name='Sarlavha')
    text = models.TextField(verbose_name='Matn')

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = 'Passage'
        verbose_name_plural = "Passage'lar"

    def __str__(self):
        return self.title or f'Passage {self.order}'


class MockQuestion(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice (A/B/C/D)'),
        ('true_false_not_given', 'True / False / Not Given'),
        ('yes_no_not_given', 'Yes / No / Not Given'),
        ('fill_blank', "Bo'sh joyni to'ldirish"),
        ('sentence_completion', 'Sentence Completion'),
        ('essay', 'Essay (Writing)'),
        ('summary_completion', 'Summary Completion'),
        ('matching', 'Matching (bitta tanlov — eski)'),
        ('matching_headings', 'Matching Headings'),
        ('matching_features', 'Matching Features'),
        ('matching_info', 'Matching Information'),
        ('matching_sentences', 'Matching Sentence Endings'),
        ('classification', 'Classification'),
        ('summary_box', 'Summary + box (inline qavslar)'),
        ('notes_completion', 'Notes Completion (Listening)'),
        ('table_completion', 'Table Completion'),
        ('speaking', 'Speaking (audio yozish)'),
    ]

    test = models.ForeignKey(
        MockTest, on_delete=models.CASCADE, related_name='questions', verbose_name='Test'
    )
    question_type = models.CharField(
        max_length=30, choices=QUESTION_TYPES, default='mcq', verbose_name='Savol turi'
    )
    question_text = models.TextField(verbose_name='Savol matni')
    instruction = models.CharField(max_length=500, blank=True, verbose_name="Ko'rsatma")
    option_a = models.CharField(max_length=500, blank=True, verbose_name='Variant A')
    option_b = models.CharField(max_length=500, blank=True, verbose_name='Variant B')
    option_c = models.CharField(max_length=500, blank=True, verbose_name='Variant C')
    option_d = models.CharField(max_length=500, blank=True, verbose_name='Variant D')
    correct_answer = models.CharField(max_length=200, blank=True, verbose_name="To'g'ri javob")
    correct_answers_json = models.JSONField(default=list, blank=True)
    options_json = models.JSONField(
        default=dict, blank=True,
        help_text='Matching: {"options": [{"letter":"a","text":"..."}, ...]}',
    )
    explanation = models.TextField(blank=True, verbose_name='Tushuntirish')
    points = models.PositiveIntegerField(default=1, verbose_name='Ball')
    order = models.PositiveIntegerField(default=0, verbose_name='Tartib')
    part_number = models.PositiveSmallIntegerField(default=1, verbose_name='Part raqami')
    audio_timestamp = models.FloatField(
        null=True, blank=True, verbose_name='Audio vaqti (soniya)',
        help_text='Listening: shu soniyadan audio ijro etiladi',
    )

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = 'Savol'
        verbose_name_plural = 'Savollar'

    def __str__(self):
        return f'{self.test.title} — #{self.order}'

    def get_choice_options(self):
        opts = self.options_json or {}
        if isinstance(opts, dict) and opts.get('options'):
            return opts['options']
        return self.get_mcq_options()

    def get_mcq_options(self):
        options = []
        for letter, value in [('a', self.option_a), ('b', self.option_b), ('c', self.option_c), ('d', self.option_d)]:
            if value:
                options.append({'letter': letter, 'text': value})
        return options

    def get_tfng_options(self):
        return [
            {'letter': 'a', 'text': self.option_a or 'True'},
            {'letter': 'b', 'text': self.option_b or 'False'},
            {'letter': 'c', 'text': self.option_c or 'Not Given'},
        ]

    def get_ynng_options(self):
        return [
            {'letter': 'a', 'text': self.option_a or 'Yes'},
            {'letter': 'b', 'text': self.option_b or 'No'},
            {'letter': 'c', 'text': self.option_c or 'Not Given'},
        ]

    def is_choice_type(self):
        return self.question_type in (
            'mcq', 'true_false_not_given', 'yes_no_not_given', 'matching',
        )

    def is_textarea_type(self):
        return self.question_type == 'essay'

    def is_matching_question(self):
        return is_matching_type(self.question_type)

    def is_multi_matching(self):
        return is_multi_matching_type(self.question_type)

    def get_matching_fields(self, user_answer=None):
        return build_matching_fields(self, user_answer)

    def get_matching_ref_options(self):
        return get_matching_ref_options(self)

    def get_matching_ref_title(self):
        return matching_ref_title(self.question_type)

    def get_listening_inline_parts(self):
        """Listening UI: matn ichida [1] yoki ______ bo'sh joylar."""
        qtypes = (
            'fill_blank', 'sentence_completion', 'summary_completion',
            'notes_completion', 'table_completion',
        )
        if self.question_type not in qtypes:
            return []
        text = self.question_text or ''
        pattern = re.compile(r'\[(\d+)\]')
        if pattern.search(text):
            parts = []
            last = 0
            for match in pattern.finditer(text):
                if match.start() > last:
                    parts.append({'type': 'text', 'content': text[last:match.start()]})
                parts.append({'type': 'input', 'num': match.group(1)})
                last = match.end()
            if last < len(text):
                parts.append({'type': 'text', 'content': text[last:]})
            return parts
        for sep in ('______', '_____', '____', '___'):
            if sep in text:
                before, after = text.split(sep, 1)
                parts = []
                if before:
                    parts.append({'type': 'text', 'content': before})
                parts.append({'type': 'input', 'num': str(self.order)})
                if after:
                    parts.append({'type': 'text', 'content': after})
                return parts
        if text.strip():
            return [
                {'type': 'text', 'content': text.rstrip() + ' '},
                {'type': 'input', 'num': str(self.order)},
            ]
        return []

    def get_bracket_segments(self):
        """[1], [2] bo'sh joylari — summary_box, notes_completion, table_completion."""
        if self.question_type not in ('summary_box', 'notes_completion', 'table_completion'):
            return []
        pattern = re.compile(r'\[(\d+)\]')
        segments = []
        last = 0
        for match in pattern.finditer(self.question_text or ''):
            if match.start() > last:
                segments.append({'type': 'text', 'value': self.question_text[last:match.start()]})
            segments.append({'type': 'blank', 'num': match.group(1)})
            last = match.end()
        if last < len(self.question_text or ''):
            segments.append({'type': 'text', 'value': self.question_text[last:]})
        return segments

    def gradable_slot_count(self):
        if self.is_multi_matching():
            correct = self.correct_answers_json if isinstance(self.correct_answers_json, dict) else {}
            if correct:
                return len(correct)
            return len(self.get_matching_fields())
        if self.question_type == 'summary_box':
            answers = self.correct_answers_json or []
            if isinstance(answers, list) and answers:
                return len(answers)
            return len([s for s in self.get_bracket_segments() if s['type'] == 'blank']) or 1
        if self.question_type in ('notes_completion', 'table_completion'):
            answers = self.correct_answers_json or []
            if isinstance(answers, list) and answers:
                return len(answers)
            return len([s for s in self.get_bracket_segments() if s['type'] == 'blank']) or 1
        return 1

    def get_summary_segments(self):
        """Matn ichidagi [1], [2] bo'sh joylarni ajratadi."""
        if self.question_type != 'summary_box':
            return []
        pattern = re.compile(r'\[(\d+)\]')
        segments = []
        last = 0
        for match in pattern.finditer(self.question_text or ''):
            if match.start() > last:
                segments.append({'type': 'text', 'value': self.question_text[last:match.start()]})
            segments.append({'type': 'blank', 'num': match.group(1)})
            last = match.end()
        if last < len(self.question_text or ''):
            segments.append({'type': 'text', 'value': self.question_text[last:]})
        return segments

    def get_summary_option_list(self):
        opts = self.options_json or {}
        return opts.get('word_list', [])


class MockAttempt(models.Model):
    session_key = models.CharField(max_length=64, db_index=True)
    test = models.ForeignKey(
        MockTest, on_delete=models.CASCADE, related_name='attempts', verbose_name='Test'
    )
    answers_json = models.JSONField(default=dict, blank=True)
    score_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    correct_count = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    is_finished = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    ielts_band = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True, verbose_name='IELTS band'
    )

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Test urinishi'
        verbose_name_plural = 'Test urinishlari'

    def __str__(self):
        return f'{self.test.title} — {self.session_key[:8]}'
