"""Test javoblarini tekshirish va ball berish."""
from decimal import Decimal

from mock_tests.matching_utils import (
    MATCHING_TYPES,
    is_multi_matching_type,
    parse_user_matching_answer,
)
from mock_tests.mcq_utils import format_mcq_letters, get_mcq_correct_letters, parse_mcq_letters, score_mcq

from .answer_normalizer import (
    collect_acceptable_answers,
    match_text_answer,
    normalize_choice,
    normalize_text,
    score_extended_text,
)
from .band_score import earned_ratio_to_band
from .gradable import question_total_points, total_gradable_slots
from .slots import list_gradable_slots, slot_correct_for_scoring


def _scores_as_blanks(question):
    if question.question_type in ('notes_completion', 'table_completion', 'summary_box'):
        return True
    if question.question_type in ('sentence_completion', 'summary_completion', 'fill_blank'):
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
    if question.question_type == 'mcq':
        letters = get_mcq_correct_letters(question)
        if letters:
            return format_mcq_letters(letters)
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


def _summary_word_bank(question):
    if question.question_type != 'summary_box':
        return []
    return question.get_summary_option_list()


def _summary_letter_to_word(question, letter):
    bank = _summary_word_bank(question)
    if not letter or not bank:
        return letter
    s = str(letter).strip().lower()
    if len(s) == 1 and s.isalpha():
        idx = ord(s) - ord('a')
        if 0 <= idx < len(bank):
            return str(bank[idx])
    return letter


def _summary_acceptable_variants(question, ans):
    variants = [str(ans)]
    bank = _summary_word_bank(question)
    ans_s = str(ans).strip()
    if not bank:
        return variants
    if len(ans_s) == 1 and ans_s.lower().isalpha():
        word = _summary_letter_to_word(question, ans_s)
        if word != ans_s:
            variants.append(str(word))
    else:
        for i, word in enumerate(bank):
            if str(word).strip().lower() == ans_s.lower():
                variants.append(chr(ord('a') + i))
                break
    return variants


def format_summary_box_answer_display(question, ans):
    """Natija: A–I harfi yoki matn."""
    bank = _summary_word_bank(question)
    ans_s = str(ans).strip()
    if not ans_s:
        return '—'
    if len(ans_s) == 1 and ans_s.lower().isalpha():
        return ans_s.lower()
    for i, word in enumerate(bank):
        if str(word).strip().lower() == ans_s.lower():
            return chr(ord('a') + i)
    return ans_s


def _match_summary_blank(question, user_val, correct_ans):
    user_word = _summary_letter_to_word(question, user_val)
    acceptable = _summary_acceptable_variants(question, correct_ans)
    return match_text_answer(user_word, acceptable) or match_text_answer(user_val, acceptable)


def score_blanks(question, user_answer):
    """notes_completion, table_completion, summary_box — har blank uchun 0..1."""
    slots = [s for s in list_gradable_slots(question) if s.kind == 'blank']
    if not slots:
        return 0.0, 0, '', ''

    blanks = _blank_map_from_user(user_answer)
    got = 0
    user_parts = []
    correct_parts = []
    for slot in slots:
        user_val = blanks.get(slot.key, blanks.get(int(slot.key) if slot.key.isdigit() else slot.key, ''))
        user_parts.append(str(user_val).strip() or '—')
        raw_correct = slot_correct_for_scoring(question, slot)
        correct_parts.append(slot.correct)
        if question.question_type == 'summary_box':
            ok = _match_summary_blank(question, user_val, raw_correct)
        else:
            ok = match_text_answer(user_val, [raw_correct]) if raw_correct else False
        if ok:
            got += 1

    total = len(slots)
    display_user = '; '.join(user_parts)
    display_correct = '; '.join(correct_parts)
    fraction = got / total if total else 0.0
    return fraction, got, display_user, display_correct


def _blank_slot_pairs(question):
    """(blank_num, display_correct) — list_gradable_slots ga mos."""
    return [
        (slot.key, slot.correct)
        for slot in list_gradable_slots(question)
        if slot.kind == 'blank'
    ]


def _matching_slot_pairs(question):
    return [
        (slot.key, slot.correct)
        for slot in list_gradable_slots(question)
        if slot.kind == 'matching'
    ]


def _question_detail_meta(question):
    return {
        'question_type': question.question_type,
        'question_type_label': question.get_result_type_label(),
    }


def _dock_buttons_by_question(questions):
    from mock_tests.views import _build_blank_buttons

    buttons, _ = _build_blank_buttons(list(questions))
    by_q = {}
    for btn in buttons:
        by_q.setdefault(btn['question_id'], []).append(btn)
    return by_q


def _ielts_num_for_slot(question, slot, dock_by_question=None):
    """Dock bilan bir xil test raqami [N]."""
    if dock_by_question:
        for btn in dock_by_question.get(question.id, []):
            if slot.kind in ('blank', 'matching'):
                if btn['is_blank'] and str(btn['blank_key']) == str(slot.key):
                    return btn['num']
            elif not btn['is_blank']:
                if str(btn['num']) == str(slot.display_num):
                    return btn['num']
                if slot.kind == 'single' and len(dock_by_question.get(question.id, [])) == 1:
                    return btn['num']
    num = slot.display_num
    return int(num) if str(num).isdigit() else num


def _detail_label(question, ielts_num):
    """Natija: tizimdagi tartib + testdagi [N] raqam."""
    if ielts_num is None:
        return f'Savol {question.order}'
    return f'Savol {question.order} — [{ielts_num}]'


def expand_question_details(question, user_answer, dock_by_question=None):
    """Har bir baholanadigan slot uchun alohida natija qatori."""
    qtype = question.question_type
    slot_pt = question_total_points(question) / max(question.gradable_slot_count(), 1)
    rows = []

    blank_slots = [s for s in list_gradable_slots(question) if s.kind == 'blank']
    if blank_slots:
        blanks = _blank_map_from_user(user_answer)
        for slot in blank_slots:
            user_val = blanks.get(slot.key, blanks.get(int(slot.key) if slot.key.isdigit() else slot.key, ''))
            raw_correct = slot_correct_for_scoring(question, slot)
            if question.question_type == 'summary_box':
                ok = _match_summary_blank(question, user_val, raw_correct)
                user_display = format_summary_box_answer_display(question, user_val) if user_val else '—'
            else:
                ok = match_text_answer(user_val, [raw_correct]) if raw_correct else False
                user_display = str(user_val).strip() or '—'
            rows.append({
                'order': int(slot.display_num) if str(slot.display_num).isdigit() else slot.display_num,
                'question_order': question.order,
                'label': _detail_label(question, _ielts_num_for_slot(question, slot, dock_by_question)),
                'is_correct': ok,
                'earned_points': round(slot_pt if ok else 0.0, 2),
                'max_points': round(slot_pt, 2),
                'user_answer_display': user_display,
                'correct_answer': slot.correct,
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
        matching_slots = [s for s in list_gradable_slots(question) if s.kind == 'matching']
        for slot in matching_slots:
            user_val = user_map.get(slot.key, '')
            corr = slot.correct
            ok = normalize_choice(user_val) == normalize_choice(corr) if corr else False
            rows.append({
                'order': int(slot.display_num) if str(slot.display_num).isdigit() else slot.display_num,
                'question_order': question.order,
                'label': _detail_label(question, _ielts_num_for_slot(question, slot, dock_by_question)),
                'is_correct': ok,
                'earned_points': round(slot_pt if ok else 0.0, 2),
                'max_points': round(slot_pt, 2),
                'user_answer_display': user_val or '—',
                'correct_answer': corr or '—',
                'explanation': question.explanation,
                **_question_detail_meta(question),
            })
        return rows

    mcq_slots = [s for s in list_gradable_slots(question) if s.kind == 'mcq_letter']
    if mcq_slots:
        user_letters = parse_mcq_letters(user_answer)
        wrong_picks = [letter for letter in user_letters if letter not in {s.correct for s in mcq_slots if s.correct}]
        wrong_iter = iter(wrong_picks)
        for slot in mcq_slots:
            letter = slot.correct
            ok = bool(letter) and letter in user_letters
            rows.append({
                'order': int(slot.display_num) if str(slot.display_num).isdigit() else slot.display_num,
                'question_order': question.order,
                'label': _detail_label(question, _ielts_num_for_slot(question, slot, dock_by_question)),
                'is_correct': ok,
                'earned_points': round(slot_pt if ok else 0.0, 2),
                'max_points': round(slot_pt, 2),
                'user_answer_display': letter if ok else next(wrong_iter, '—'),
                'correct_answer': letter or '—',
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
    if not correct_norm or correct_norm == '—':
        correct_norm = format_correct_display(question) or '—'
    q_pt = question_total_points(question)
    single_slots = list_gradable_slots(question)
    single_slot = single_slots[0] if single_slots else None
    ielts_num = (
        _ielts_num_for_slot(question, single_slot, dock_by_question)
        if single_slot else question.order
    )
    rows.append({
        'order': question.order,
        'question_order': question.order,
        'label': _detail_label(question, ielts_num),
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
    slots = [s for s in list_gradable_slots(question) if s.kind == 'matching']
    user_map = parse_user_matching_answer(user_answer)
    if not slots:
        return 0.0, 0, 0, format_answer_display(user_map), ''

    got = 0
    for slot in slots:
        user_val = user_map.get(slot.key, '')
        if slot.correct and normalize_choice(user_val) == normalize_choice(slot.correct):
            got += 1
    total = len(slots)
    fraction = got / total if total else 0.0
    display_correct = format_correct_display(question) or '; '.join(
        f'{s.key} → {s.correct}' for s in slots if s.correct
    )
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
        user = normalize_text(user_answer) if not isinstance(user_answer, dict) else format_answer_display(user_answer)
        ok = match_text_answer(user_answer, acceptable) if not isinstance(user_answer, dict) else False
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
    dock_by_question = _dock_buttons_by_question(questions)

    for question in questions:
        qid = str(question.id)
        user_answer = answers.get(qid, '')
        q_total = question_total_points(question)
        total_points += q_total

        earned = score_question_points(question, user_answer)
        earned_points += earned

        for row in expand_question_details(question, user_answer, dock_by_question):
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
