"""Testdagi baholanadigan birliklar (blank, matching qatori) — savol emas."""
from .slots import list_gradable_slots


def total_gradable_slots(questions):
    return sum(q.gradable_slot_count() for q in questions)


def question_total_points(question):
    slots = question.gradable_slot_count()
    if slots <= 1:
        return float(question.points or 1)
    return float(slots)


def count_filled_slots(question, user_answer):
    slots = list_gradable_slots(question)
    if len(slots) == 1 and slots[0].kind == 'single':
        if user_answer is None or user_answer == '':
            return 0
        if isinstance(user_answer, dict):
            return 1 if any(v and str(v).strip() for v in user_answer.values()) else 0
        return 1 if str(user_answer).strip() else 0

    if not isinstance(user_answer, dict):
        return 0

    filled = 0
    for slot in slots:
        if slot.kind in ('blank', 'matching'):
            val = user_answer.get(slot.key, user_answer.get(int(slot.key) if slot.key.isdigit() else slot.key, ''))
            if val and str(val).strip():
                filled += 1
    return filled


def count_filled_slots_for_test(questions, answers):
    total = 0
    for q in questions:
        total += count_filled_slots(q, answers.get(str(q.pk), ''))
    return total
