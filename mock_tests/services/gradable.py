"""Testdagi baholanadigan birliklar (blank, matching qatori) — savol emas."""


def total_gradable_slots(questions):
    return sum(q.gradable_slot_count() for q in questions)


def question_total_points(question):
    slots = question.gradable_slot_count()
    if slots <= 1:
        return float(question.points or 1)
    return float(slots)


def count_filled_slots(question, user_answer):
    slots = question.gradable_slot_count()
    if slots <= 1:
        if user_answer is None or user_answer == '':
            return 0
        if isinstance(user_answer, dict):
            return 1 if any(v and str(v).strip() for v in user_answer.values()) else 0
        return 1 if str(user_answer).strip() else 0

    if not isinstance(user_answer, dict):
        return 0

    if question.question_type in ('notes_completion', 'table_completion', 'summary_box'):
        blank_nums = [
            s['num'] for s in question.get_bracket_segments() if s['type'] == 'blank'
        ]
        if not blank_nums and question.question_type == 'summary_box':
            blank_nums = [
                s['num'] for s in question.get_summary_segments() if s['type'] == 'blank'
            ]
        if not blank_nums:
            answers = question.correct_answers_json or []
            blank_nums = [str(i) for i in range(1, len(answers) + 1)]
        return sum(
            1 for num in blank_nums
            if str(user_answer.get(str(num), user_answer.get(num, ''))).strip()
        )

    if question.is_multi_matching():
        correct = question.correct_answers_json if isinstance(question.correct_answers_json, dict) else {}
        keys = list(correct.keys()) if correct else [f['num'] for f in question.get_matching_fields()]
        return sum(
            1 for k in keys
            if str(user_answer.get(str(k), user_answer.get(k, ''))).strip()
        )

    return sum(1 for v in user_answer.values() if v and str(v).strip())


def count_filled_slots_for_test(questions, answers):
    total = 0
    for q in questions:
        total += count_filled_slots(q, answers.get(str(q.pk), ''))
    return total
