"""Test javoblarini tekshirish va ball berish."""
from decimal import Decimal

from mock_tests.matching_utils import (
    MATCHING_TYPES,
    is_multi_matching_type,
    parse_user_matching_answer,
)
from mock_tests.mcq_utils import score_mcq

from .answer_normalizer import (
    collect_acceptable_answers,
    match_text_answer,
    normalize_choice,
    normalize_text,
    score_extended_text,
)
from .band_score import earned_ratio_to_band
from .gradable import question_total_points, total_gradable_slots


def _scores_as_blanks(question):
    if question.question_type in ('notes_completion', 'table_completion', 'summary_box'):
        return True
    if question.question_type in ('sentence_completion', 'summary_completion'):
        return question.uses_bracket_blanks()
    return False


def format_answer_display(user_answer):
    if isinstance(user_answer, dict):
        parts = []
        for key in sorted(user_answer.keys(), key=lambda k: int(k) if str(k).isdigit() else str(k)):
            val = user_answer[key]
            if val:
                parts.append(f'{key}: {val}')
        return '; '.join(parts) if parts else '—'
    if user_answer is None or user_answer == '':
        return '—'
    return str(user_answer)


def format_correct_display(question):
    if is_multi_matching_type(question.question_type):
        correct = question.correct_answers_json if isinstance(question.correct_answers_json, dict) else {}
        if correct:
            return '; '.join(
                f'{k} → {v}' for k, v in sorted(
                    correct.items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else str(x[0])
                )
            )
    if question.question_type == 'summary_box':
        answers = question.correct_answers_json or []
        if isinstance(answers, list):
            return ', '.join(str(a) for a in answers)
    acceptable = collect_acceptable_answers(question)
    if acceptable:
        return ' / '.join(acceptable)
    return question.correct_answer or ''


def _blank_map_from_user(user_answer):
    if isinstance(user_answer, dict):
        return user_answer
    return {}


def _acceptable_blanks_list(question):
    raw = question.correct_answers_json or []
    if not isinstance(raw, list):
        return []
    return [str(a) for a in raw if a is not None and str(a).strip()]


def _sorted_blank_nums(segments):
    nums = [s['num'] for s in segments if s['type'] == 'blank']
    return sorted(nums, key=lambda n: int(n) if str(n).isdigit() else str(n))


def score_blanks(question, user_answer):
    """notes_completion, table_completion, summary_box — har blank uchun 0..1."""
    acceptable = _acceptable_blanks_list(question)
    blanks = _blank_map_from_user(user_answer)
    segments = question.get_bracket_segments()
    if question.question_type == 'summary_box':
        segments = question.get_summary_segments()
    blank_nums = _sorted_blank_nums(segments)
    if not blank_nums:
        blank_nums = [str(i) for i in range(1, len(acceptable) + 1)]

    if not acceptable:
        return 0.0, 0, '', ''

    got = 0
    user_parts = []
    for idx, ans in enumerate(acceptable):
        num = blank_nums[idx] if idx < len(blank_nums) else str(idx + 1)
        user_val = blanks.get(str(num), blanks.get(num, ''))
        user_parts.append(str(user_val).strip() or '—')
        if match_text_answer(user_val, [ans]):
            got += 1

    total = len(acceptable)
    display_user = '; '.join(user_parts)
    display_correct = '; '.join(acceptable)
    fraction = got / total if total else 0.0
    return fraction, got, display_user, display_correct


def _blank_slot_pairs(question):
    """(blank_num, acceptable_answer) ro'yxati."""
    acceptable = _acceptable_blanks_list(question)
    segments = question.get_bracket_segments()
    if question.question_type == 'summary_box':
        segments = question.get_summary_segments()
    blank_nums = _sorted_blank_nums(segments)
    if not blank_nums:
        blank_nums = [str(i) for i in range(1, len(acceptable) + 1)]
    pairs = []
    for idx, ans in enumerate(acceptable):
        num = blank_nums[idx] if idx < len(blank_nums) else str(idx + 1)
        pairs.append((str(num), str(ans)))
    return pairs


def _matching_slot_pairs(question):
    correct = question.correct_answers_json if isinstance(question.correct_answers_json, dict) else {}
    if correct:
        return [(str(k), str(v)) for k, v in sorted(
            correct.items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else str(x[0])
        )]
    fields = question.get_matching_fields()
    return [(str(f['num']), '') for f in fields]


def _question_detail_meta(question):
    return {
        'question_type': question.question_type,
        'question_type_label': question.get_result_type_label(),
    }


def expand_question_details(question, user_answer):
    """Har bir baholanadigan slot uchun alohida natija qatori."""
    qtype = question.question_type
    slot_pt = question_total_points(question) / max(question.gradable_slot_count(), 1)
    rows = []

    if qtype in ('notes_completion', 'table_completion', 'summary_box') or (
        qtype in ('sentence_completion', 'summary_completion') and question.uses_bracket_blanks()
    ):
        blanks = _blank_map_from_user(user_answer)
        for num, ans in _blank_slot_pairs(question):
            user_val = blanks.get(num, blanks.get(int(num) if str(num).isdigit() else num, ''))
            ok = match_text_answer(user_val, [ans])
            rows.append({
                'order': num,
                'question_order': question.order,
                'label': f'Savol {question.order} — [{num}]',
                'is_correct': ok,
                'earned_points': round(slot_pt if ok else 0.0, 2),
                'max_points': round(slot_pt, 2),
                'user_answer_display': str(user_val).strip() or '—',
                'correct_answer': ans,
                'explanation': question.explanation,
                **_question_detail_meta(question),
            })
        return rows

    if qtype == 'essay':
        from mock_tests.services.answer_normalizer import count_words, score_extended_text

        text = str(user_answer or '').strip()
        earned = score_question_points(question, user_answer)
        words = count_words(text)
        target = score_extended_text(text, min_words=50, target_words=250)
        rows.append({
            'order': question.order,
            'question_order': question.order,
            'label': f'Task {question.order}',
            'is_correct': target >= 0.5,
            'earned_points': round(earned, 2),
            'max_points': round(question_total_points(question), 2),
            'user_answer_display': text or '—',
            'correct_answer': f'Kamida 50 so\'z (yozilgan: {words})',
            'explanation': question.explanation,
            'is_essay': True,
            **_question_detail_meta(question),
        })
        return rows

    if qtype in MATCHING_TYPES:
        from mock_tests.matching_utils import parse_user_matching_answer
        user_map = parse_user_matching_answer(user_answer)
        for num, corr in _matching_slot_pairs(question):
            user_val = user_map.get(num, '')
            ok = normalize_choice(user_val) == normalize_choice(corr) if corr else False
            rows.append({
                'order': num,
                'question_order': question.order,
                'label': f'Savol {question.order} — {num}',
                'is_correct': ok,
                'earned_points': round(slot_pt if ok else 0.0, 2),
                'max_points': round(slot_pt, 2),
                'user_answer_display': user_val or '—',
                'correct_answer': corr or '—',
                'explanation': question.explanation,
                **_question_detail_meta(question),
            })
        return rows

    earned = score_question_points(question, user_answer)
    is_correct, user_norm, correct_norm = check_question_answer(question, user_answer)
    if not user_norm or user_norm == '—':
        user_display = format_answer_display(user_answer)
    else:
        user_display = user_norm
    if not correct_norm:
        correct_norm = format_correct_display(question) or '—'
    q_pt = question_total_points(question)
    rows.append({
        'order': question.order,
        'question_order': question.order,
        'label': f'Savol {question.order}',
        'is_correct': is_correct,
        'earned_points': round(earned, 2),
        'max_points': round(q_pt, 2),
        'user_answer_display': user_display,
        'correct_answer': correct_norm,
        'explanation': question.explanation,
        **_question_detail_meta(question),
    })
    return rows


def score_matching_partial(question, user_answer):
    correct = question.correct_answers_json if isinstance(question.correct_answers_json, dict) else {}
    if not correct:
        user_map = parse_user_matching_answer(user_answer)
        return 0.0, 0, 0, format_answer_display(user_map), ''

    user_map = parse_user_matching_answer(user_answer)
    got = 0
    for k, v in correct.items():
        user_val = user_map.get(str(k), '')
        if normalize_choice(user_val) == normalize_choice(v):
            got += 1
    total = len(correct)
    fraction = got / total if total else 0.0
    display_correct = format_correct_display(question) or str(correct)
    return fraction, got, total, format_answer_display(user_map), display_correct


def check_question_answer(question, user_answer):
    """Bitta savol: (to'liq to'g'rimi, user_display, correct_display)."""
    qtype = question.question_type

    if qtype == 'mcq':
        _, ok, user_disp, correct_disp = score_mcq(question, user_answer)
        return ok, user_disp, correct_disp

    if qtype in ('true_false_not_given', 'yes_no_not_given', 'matching'):
        correct = normalize_choice(question.correct_answer)
        user = normalize_choice(user_answer)
        ok = bool(correct) and user == correct
        return ok, user or '—', correct

    if qtype in MATCHING_TYPES:
        frac, _, _, user_disp, correct_disp = score_matching_partial(question, user_answer)
        return frac >= 1.0, user_disp, correct_disp

    if qtype in ('fill_blank', 'sentence_completion', 'summary_completion') and not _scores_as_blanks(question):
        acceptable = collect_acceptable_answers(question)
        user = normalize_text(user_answer)
        ok = match_text_answer(user_answer, acceptable)
        return ok, user or '—', ' / '.join(acceptable)

    if _scores_as_blanks(question):
        frac, _, user_disp, correct_disp = score_blanks(question, user_answer)
        return frac >= 1.0, user_disp, correct_disp

    if qtype == 'essay':
        text = str(user_answer or '').strip()
        frac = score_extended_text(text, min_words=50, target_words=250)
        ok = frac >= 0.5
        return ok, text[:150] or '—', 'Writing (50+ so\'z)'

    return False, normalize_text(user_answer), ''


def score_question_points(question, user_answer):
    """Savol uchun 0..question.points ball (qisman ball bilan)."""
    qtype = question.question_type
    points = float(question.points or 1)

    if qtype in MATCHING_TYPES:
        frac, _, _, _, _ = score_matching_partial(question, user_answer)
        return question_total_points(question) * frac

    if _scores_as_blanks(question):
        frac, _, _, _ = score_blanks(question, user_answer)
        return question_total_points(question) * frac

    if qtype == 'mcq':
        frac, _, _, _ = score_mcq(question, user_answer)
        return points * frac

    if qtype == 'essay':
        frac = score_extended_text(str(user_answer or ''), min_words=50, target_words=250)
        return points * frac

    ok, _, _ = check_question_answer(question, user_answer)
    return points if ok else 0.0


def score_attempt(attempt, questions):
    answers = attempt.answers_json or {}
    total_points = 0.0
    earned_points = 0.0
    correct_slots = 0
    details = []

    for question in questions:
        qid = str(question.id)
        user_answer = answers.get(qid, '')
        q_total = question_total_points(question)
        total_points += q_total

        earned = score_question_points(question, user_answer)
        earned_points += earned

        for row in expand_question_details(question, user_answer):
            if row['is_correct']:
                correct_slots += 1
            details.append({
                'question_id': question.id,
                'order': row['order'],
                'question_order': row.get('question_order', question.order),
                'label': row.get('label', f"Savol {row['order']}"),
                'question_type': row.get('question_type', question.question_type),
                'question_type_label': row.get('question_type_label', question.get_result_type_label()),
                'is_correct': row['is_correct'],
                'earned_points': row['earned_points'],
                'max_points': row['max_points'],
                'user_answer_display': row['user_answer_display'],
                'correct_answer': row['correct_answer'],
                'explanation': row['explanation'],
                'is_essay': row.get('is_essay', False),
            })

    total_questions = total_gradable_slots(questions)
    if total_points:
        score_percent = Decimal(earned_points * 100) / Decimal(total_points)
    elif total_questions:
        score_percent = Decimal(correct_slots * 100) / Decimal(total_questions)
    else:
        score_percent = Decimal('0')

    band = None
    if attempt.test.test_type in ('reading', 'listening') and total_points:
        band = earned_ratio_to_band(earned_points, total_points)

    return {
        'correct_count': correct_slots,
        'earned_points': round(earned_points, 2),
        'total_points': round(total_points, 2),
        'ielts_band': band,
        'total_questions': total_questions,
        'score_percent': score_percent.quantize(Decimal('0.01')),
        'passed': float(score_percent) >= attempt.test.passing_score,
        'details': details,
    }
