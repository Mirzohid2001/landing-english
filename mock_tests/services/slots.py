"""Baholanadigan slotlar — dock, ball va natija uchun yagona manba."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from mock_tests.mcq_utils import get_mcq_correct_letters
from mock_tests.matching_utils import is_multi_matching_type

BLANK_TYPES = (
    'summary_box',
    'notes_completion',
    'table_completion',
    'sentence_completion',
    'summary_completion',
    'fill_blank',
)

FILL_SINGLE_BLANK_TYPES = ('fill_blank', 'sentence_completion', 'summary_completion')


@dataclass(frozen=True)
class GradableSlot:
    """Bitta baholanadigan bo'sh joy / matching qatori / MCQ harfi."""

    kind: str  # blank | matching | mcq_letter | single
    key: str  # user_answer dict kaliti; single uchun ''
    display_num: str
    correct: str = ''


def _sort_num_key(value):
    s = str(value)
    return int(s) if s.isdigit() else s


def _answers_list(question) -> List[str]:
    raw = question.correct_answers_json or []
    if not isinstance(raw, list):
        return []
    return [str(a) for a in raw if a is not None and str(a).strip()]


def _bracket_nums(question) -> List[str]:
    if question.question_type == 'summary_box':
        segments = question.get_summary_segments()
    elif question.question_type in BLANK_TYPES:
        segments = question.get_bracket_segments()
    else:
        return []
    nums = [str(s['num']) for s in segments if s.get('type') == 'blank']
    return sorted(nums, key=_sort_num_key)


def _summary_display_answer(question, ans: str) -> str:
    from mock_tests.services.scoring import format_summary_box_answer_display

    return format_summary_box_answer_display(question, ans)


def _matching_slots(question) -> List[GradableSlot]:
    fields = question.get_matching_fields()
    correct = question.correct_answers_json if isinstance(question.correct_answers_json, dict) else {}
    slots = []
    if fields:
        for field in fields:
            num = str(field['num'])
            corr = correct.get(num, correct.get(int(num) if num.isdigit() else num, ''))
            slots.append(GradableSlot(
                kind='matching',
                key=num,
                display_num=num,
                correct=str(corr or ''),
            ))
        return slots
    if correct:
        for num, corr in sorted(correct.items(), key=lambda x: _sort_num_key(x[0])):
            slots.append(GradableSlot(
                kind='matching',
                key=str(num),
                display_num=str(num),
                correct=str(corr),
            ))
    return slots


def _mcq_multi_slots(question) -> List[GradableSlot]:
    select_count = question.get_mcq_select_count()
    letters = get_mcq_correct_letters(question)
    count = len(letters) if letters else select_count
    slots = []
    for idx in range(count):
        disp = str(question.order + idx)
        letter = letters[idx] if idx < len(letters) else ''
        slots.append(GradableSlot(
            kind='mcq_letter',
            key=disp,
            display_num=disp,
            correct=letter,
        ))
    return slots


def _blank_slots(question) -> List[GradableSlot]:
    nums = _bracket_nums(question)
    answers = _answers_list(question)
    if nums:
        slots = []
        for idx, num in enumerate(nums):
            ans = answers[idx] if idx < len(answers) else ''
            display_ans = _summary_display_answer(question, ans) if question.question_type == 'summary_box' else ans
            slots.append(GradableSlot(
                kind='blank',
                key=str(num),
                display_num=str(num),
                correct=display_ans,
            ))
        return slots
    if answers and question.question_type not in FILL_SINGLE_BLANK_TYPES:
        return [
            GradableSlot(
                kind='blank',
                key=str(idx + 1),
                display_num=str(idx + 1),
                correct=ans,
            )
            for idx, ans in enumerate(answers)
        ]
    primary = answers[0] if answers else (question.correct_answer or '')
    return [GradableSlot(
        kind='single',
        key='',
        display_num=str(question.order),
        correct=str(primary or ''),
    )]


def list_gradable_slots(question) -> List[GradableSlot]:
    """Savol uchun barcha baholanadigan slotlar (tartiblangan)."""
    if question.question_type in BLANK_TYPES:
        return _blank_slots(question)
    if is_multi_matching_type(question.question_type):
        slots = _matching_slots(question)
        if slots:
            return slots
    if question.question_type == 'mcq' and question.get_mcq_select_count() > 1:
        return _mcq_multi_slots(question)
    return [GradableSlot(
        kind='single',
        key='',
        display_num=str(question.order),
        correct=str(question.correct_answer or ''),
    )]


def gradable_slot_count(question) -> int:
    slots = list_gradable_slots(question)
    return max(1, len(slots))


def slot_correct_for_scoring(question, slot: GradableSlot) -> str:
    """Natija/scoring uchun xom to'g'ri javob (summary_box harfi emas)."""
    if slot.kind != 'blank' or question.question_type != 'summary_box':
        return slot.correct
    answers = _answers_list(question)
    nums = _bracket_nums(question)
    if slot.key in nums:
        idx = nums.index(slot.key)
        if idx < len(answers):
            return answers[idx]
    return slot.correct
