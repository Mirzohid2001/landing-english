"""Test javoblarini tekshirish va ball berish."""
from decimal import Decimal

from mock_tests.matching_utils import (
    MATCHING_TYPES,
    is_multi_matching_type,
    parse_user_matching_answer,
)

from .answer_normalizer import (
    collect_acceptable_answers,
    match_text_answer,
    normalize_choice,
    normalize_text,
    score_extended_text,
)
from .band_score import earned_ratio_to_band


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


def score_blanks(question, user_answer):
    """notes_completion, table_completion, summary_box — har blank uchun 0..1."""
    acceptable = _acceptable_blanks_list(question)
    blanks = _blank_map_from_user(user_answer)
    if not acceptable:
        return 0.0, 0, '', ''

    got = 0
    user_parts = []
    for i, ans in enumerate(acceptable, start=1):
        user_val = blanks.get(str(i), blanks.get(i, ''))
        user_parts.append(str(user_val).strip() or '—')
        if match_text_answer(user_val, [ans]):
            got += 1

    total = len(acceptable)
    display_user = '; '.join(user_parts)
    display_correct = '; '.join(acceptable)
    fraction = got / total if total else 0.0
    return fraction, got, display_user, display_correct


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

    if qtype in ('mcq', 'true_false_not_given', 'yes_no_not_given', 'matching'):
        correct = normalize_choice(question.correct_answer)
        user = normalize_choice(user_answer)
        ok = bool(correct) and user == correct
        return ok, user or '—', correct

    if qtype in MATCHING_TYPES:
        frac, _, _, user_disp, correct_disp = score_matching_partial(question, user_answer)
        return frac >= 1.0, user_disp, correct_disp

    if qtype in ('fill_blank', 'sentence_completion', 'summary_completion'):
        acceptable = collect_acceptable_answers(question)
        user = normalize_text(user_answer)
        ok = match_text_answer(user_answer, acceptable)
        return ok, user or '—', ' / '.join(acceptable)

    if qtype in ('notes_completion', 'table_completion', 'summary_box'):
        frac, _, user_disp, correct_disp = score_blanks(question, user_answer)
        return frac >= 1.0, user_disp, correct_disp

    if qtype == 'speaking':
        text = str(user_answer or '').strip()
        frac = score_extended_text(text, min_words=20, target_words=120)
        ok = frac >= 0.5
        return ok, text[:120] or '—', 'Speaking (20+ so\'z)'

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
        return points * frac

    if qtype in ('notes_completion', 'table_completion', 'summary_box'):
        frac, _, _, _ = score_blanks(question, user_answer)
        return points * frac

    if qtype == 'essay':
        frac = score_extended_text(str(user_answer or ''), min_words=50, target_words=250)
        return points * frac

    if qtype == 'speaking':
        frac = score_extended_text(str(user_answer or ''), min_words=20, target_words=120)
        return points * frac

    ok, _, _ = check_question_answer(question, user_answer)
    return points if ok else 0.0


def score_attempt(attempt, questions):
    answers = attempt.answers_json or {}
    total_points = 0.0
    earned_points = 0.0
    fully_correct = 0
    details = []

    for question in questions:
        qid = str(question.id)
        user_answer = answers.get(qid, '')
        q_points = float(question.points or 1)
        total_points += q_points

        earned = score_question_points(question, user_answer)
        earned_points += earned

        is_correct, user_norm, correct_norm = check_question_answer(question, user_answer)
        if is_correct:
            fully_correct += 1

        if not user_norm or user_norm == '—':
            user_display = format_answer_display(user_answer)
        else:
            user_display = user_norm

        if not correct_norm:
            correct_norm = format_correct_display(question) or '—'

        details.append({
            'question_id': question.id,
            'order': question.order,
            'is_correct': is_correct,
            'earned_points': round(earned, 2),
            'max_points': q_points,
            'user_answer': user_answer,
            'user_answer_display': user_display,
            'correct_answer': correct_norm,
            'explanation': question.explanation,
        })

    total_questions = len(questions)
    if total_points:
        score_percent = Decimal(earned_points * 100) / Decimal(total_points)
    elif total_questions:
        score_percent = Decimal(fully_correct * 100) / Decimal(total_questions)
    else:
        score_percent = Decimal('0')

    band = None
    if attempt.test.test_type in ('reading', 'listening') and total_points:
        band = earned_ratio_to_band(earned_points, total_points)

    return {
        'correct_count': fully_correct,
        'earned_points': round(earned_points, 2),
        'total_points': round(total_points, 2),
        'ielts_band': band,
        'total_questions': total_questions,
        'score_percent': score_percent.quantize(Decimal('0.01')),
        'passed': float(score_percent) >= attempt.test.passing_score,
        'details': details,
    }
