import json
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from .models import MockTest, MockAttempt
from .services.ui_dock import attach_reading_ui_dock_labels
from .services.gradable import total_gradable_slots
from .services.slots import list_gradable_slots
from .services.scoring import score_attempt


def _ensure_session(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


MAX_DAILY_ATTEMPTS = 5


def _count_today_attempts(session_key, test):
    from django.utils import timezone
    today = timezone.now().date()
    return MockAttempt.objects.filter(
        test=test, session_key=session_key, is_finished=True,
        finished_at__date=today,
    ).count()


def _get_or_create_attempt(request, test):
    session_key = _ensure_session(request)
    attempt = MockAttempt.objects.filter(
        test=test, session_key=session_key, is_finished=False
    ).first()
    if not attempt:
        attempt = MockAttempt.objects.create(test=test, session_key=session_key)
    return attempt


def _build_blank_buttons(questions, start_num=0, sequential_only=False):
    """Footer dock — ketma-ket raqamlar; listeningda qavs/IELTS raqami afzal."""
    buttons = []
    seq_fallback = start_num
    used_nums = set()

    def _pick_num(preferred):
        nonlocal seq_fallback
        if not sequential_only and preferred is not None and preferred not in used_nums:
            used_nums.add(preferred)
            if isinstance(preferred, int):
                seq_fallback = max(seq_fallback, preferred)
            return preferred
        numeric_used = [n for n in used_nums if isinstance(n, int)]
        if numeric_used:
            seq_fallback = max(seq_fallback, max(numeric_used))
        seq_fallback += 1
        while seq_fallback in used_nums:
            seq_fallback += 1
        used_nums.add(seq_fallback)
        return seq_fallback

    def _preferred_num(value):
        if sequential_only or value is None:
            return None
        numeric_used = [n for n in used_nums if isinstance(n, int)]
        if numeric_used and isinstance(value, int) and value <= max(numeric_used):
            return None
        return value

    def _append(question_id, is_blank, blank_key='', question_order=None):
        if sequential_only:
            num = None
        elif is_blank and blank_key:
            num = int(blank_key) if str(blank_key).isdigit() else blank_key
        elif question_order is not None:
            num = _preferred_num(question_order)
        else:
            num = None
        buttons.append({
            'num': _pick_num(num),
            'question_id': question_id,
            'is_blank': is_blank,
            'blank_key': blank_key,
        })

    for q in sorted(questions, key=lambda x: (x.order, x.pk)):
        slots = list_gradable_slots(q)
        if len(slots) == 1 and slots[0].kind == 'single':
            disp = slots[0].display_num
            order_num = int(disp) if str(disp).isdigit() else disp
            _append(q.pk, False, question_order=order_num)
            continue
        for slot in slots:
            if slot.kind in ('blank', 'matching'):
                _append(q.pk, True, slot.key)
            else:
                num = slot.display_num
                order_num = int(num) if str(num).isdigit() else num
                _append(q.pk, False, question_order=order_num)
    return buttons, seq_fallback


def _build_test_dock_buttons(test, questions, start_num=0):
    """Barcha dock tugmalari — avval part bo'yicha, keyin savol tartibida."""
    parts = {}
    for q in questions:
        parts.setdefault(q.part_number or 1, []).append(q)
    sequential = test.test_type == 'reading'
    all_buttons = []
    offset = start_num
    for part_num in sorted(parts.keys()):
        qs = parts[part_num]
        buttons, offset = _build_blank_buttons(qs, offset, sequential_only=sequential)
        all_buttons.extend(buttons)
    return all_buttons, offset


def _build_instruction_groups(questions):
    """Instruction bo'yicha guruhlar — har blok uchun birinchi rasm."""
    from mock_tests.question_admin_helpers import sanitize_block_instruction

    if not questions:
        return []
    sorted_qs = sorted(questions, key=lambda q: (q.order, q.pk))
    groups = []
    current_instr = None
    bucket = []

    def flush():
        if not bucket:
            return
        block_image = next((q.image for q in bucket if q.image), None)
        instr = current_instr or ''
        groups.append({
            'instruction': instr,
            'display_instruction': sanitize_block_instruction(instr, bucket),
            'questions': list(bucket),
            'image': block_image,
        })

    for q in sorted_qs:
        instr = q.instruction or ''
        if bucket and instr != current_instr:
            flush()
            bucket = []
        current_instr = instr
        bucket.append(q)
    flush()
    return groups


def _build_part_groups(test, questions, passages):
    parts = {}
    for q in questions:
        part_num = q.part_number or 1
        parts.setdefault(part_num, []).append(q)

    passage_map = {p.order: p for p in passages}
    part_groups = []
    global_offset = 0
    sequential_dock = test.test_type == 'reading'
    for part_num in sorted(parts.keys()):
        qs = parts[part_num]
        question_count = sum(q.gradable_slot_count() for q in qs)
        blank_buttons, global_offset = _build_blank_buttons(
            qs, global_offset, sequential_only=sequential_dock,
        )
        orders = [q.order for q in qs]
        start_order = min(orders) if orders else 0
        end_order = max(orders) if orders else 0
        if blank_buttons:
            start_num, end_num = blank_buttons[0]['num'], blank_buttons[-1]['num']
            range_label = str(start_num) if start_num == end_num else f'{start_num}-{end_num}'
        else:
            range_label = f'{start_order}-{end_order}' if start_order != end_order else str(start_order)

        title = f'Task {part_num}' if test.test_type == 'writing' else f'Part {part_num}'
        audio_start_time = 0
        if test.test_type == 'listening':
            for q in qs:
                if q.audio_timestamp is not None:
                    audio_start_time = float(q.audio_timestamp)
                    break

        part_groups.append({
            'part_number': part_num,
            'passage': passage_map.get(part_num),
            'questions': qs,
            'instruction_groups': _build_instruction_groups(qs),
            'blank_buttons': blank_buttons,
            'question_count': question_count,
            'start_order': start_order,
            'end_order': end_order,
            'range_label': range_label,
            'title': title,
            'slug': f'part-{part_num}',
            'audio_start_time': audio_start_time,
        })
    return part_groups


def _questions_range_display(questions, test=None):
    if not questions:
        return '0'
    if test is not None:
        buttons, _ = _build_test_dock_buttons(test, questions)
    else:
        buttons, _ = _build_blank_buttons(questions)
    if buttons:
        start, end = buttons[0]['num'], buttons[-1]['num']
        return str(start) if start == end else f'{start}-{end}'
    orders = [q.order for q in questions]
    start, end = min(orders), max(orders)
    return f'{start}-{end}' if start != end else str(start)


def _limit_reached_response(request, test):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'limit_reached'}, status=403)
    return render(request, 'mock_tests/limit_reached.html', {'test': test, 'max': MAX_DAILY_ATTEMPTS})


def _latest_finished_attempts(session_key, test_ids):
    """Har bir test uchun sessiyadagi eng so'nggi tugallangan urinish."""
    if not test_ids:
        return {}
    attempts = MockAttempt.objects.filter(
        session_key=session_key,
        test_id__in=test_ids,
        is_finished=True,
    ).order_by('test_id', '-finished_at')
    latest = {}
    for attempt in attempts:
        if attempt.test_id not in latest:
            latest[attempt.test_id] = attempt
    return latest


def test_list(request):
    test_type = request.GET.get('type', '')
    tests_qs = MockTest.objects.filter(is_active=True)
    if test_type:
        tests_qs = tests_qs.filter(test_type=test_type)
    tests = list(tests_qs)

    session_key = _ensure_session(request)
    last_attempts = _latest_finished_attempts(session_key, [t.pk for t in tests])
    tests_with_meta = [
        {'test': t, 'last_attempt': last_attempts.get(t.pk)}
        for t in tests
    ]

    context = {
        'tests_with_meta': tests_with_meta,
        'test_type': test_type,
        'test_type_choices': MockTest.TEST_TYPES,
    }
    return render(request, 'mock_tests/list.html', context)


def test_detail(request, pk):
    test = get_object_or_404(MockTest, pk=pk, is_active=True)
    session_key = _ensure_session(request)
    today_count = _count_today_attempts(session_key, test)
    attempts_remaining = max(0, MAX_DAILY_ATTEMPTS - today_count)
    last_attempts = _latest_finished_attempts(session_key, [test.pk])
    context = {
        'test': test,
        'attempts_remaining': attempts_remaining,
        'max_daily_attempts': MAX_DAILY_ATTEMPTS,
        'last_attempt': last_attempts.get(test.pk),
    }
    return render(request, 'mock_tests/detail.html', context)


@require_http_methods(['GET', 'POST'])
def test_take(request, pk):
    test = get_object_or_404(MockTest, pk=pk, is_active=True)
    questions = list(test.questions.all())
    passages = list(test.passages.all())
    session_key = _ensure_session(request)

    if request.method == 'GET':
        if _count_today_attempts(session_key, test) >= MAX_DAILY_ATTEMPTS:
            return _limit_reached_response(request, test)

    if request.method == 'POST':
        in_progress = MockAttempt.objects.filter(
            test=test, session_key=session_key, is_finished=False,
        ).first()
        if not in_progress and _count_today_attempts(session_key, test) >= MAX_DAILY_ATTEMPTS:
            return _limit_reached_response(request, test)
        attempt = in_progress or MockAttempt.objects.create(test=test, session_key=session_key)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return JsonResponse({'success': False, 'error': 'invalid_json'}, status=400)

            if data.get('action') == 'save':
                attempt.answers_json = data.get('answers', {})
                attempt.save(update_fields=['answers_json'])
                return JsonResponse({'success': True})

            if data.get('action') == 'finish':
                attempt.answers_json = data.get('answers', {})
                result = score_attempt(attempt, questions)
                attempt.correct_count = result['correct_count']
                attempt.total_questions = result['total_questions']
                attempt.score_percent = result['score_percent']
                if result.get('ielts_band') is not None:
                    attempt.ielts_band = result['ielts_band']
                attempt.is_finished = True
                attempt.finished_at = timezone.now()
                attempt.save()
                return JsonResponse({
                    'success': True,
                    'redirect_url': f'/courses/tests/{test.pk}/result/{attempt.pk}/',
                })

        answers = {}
        for q in questions:
            answers[str(q.id)] = request.POST.get(f'q_{q.id}', '')
        attempt.answers_json = answers
        result = score_attempt(attempt, questions)
        attempt.correct_count = result['correct_count']
        attempt.total_questions = result['total_questions']
        attempt.score_percent = result['score_percent']
        if result.get('ielts_band') is not None:
            attempt.ielts_band = result['ielts_band']
        attempt.is_finished = True
        attempt.finished_at = timezone.now()
        attempt.save()
        return redirect('mock_tests:test_result', pk=test.pk, attempt_id=attempt.pk)

    attempt = _get_or_create_attempt(request, test)

    part_groups = _build_part_groups(test, questions, passages)
    saved_answers = attempt.answers_json or {}
    for q in questions:
        ua = saved_answers.get(str(q.pk), '')
        q.ui_matching_fields = q.get_matching_fields(ua)
        q.ui_matching_ref_options = q.get_matching_ref_options()
        q.ui_matching_ref_title = q.get_matching_ref_title()
        q.ui_bracket_segments = q.get_bracket_segments()
    attach_reading_ui_dock_labels(test, questions, part_groups)
    context = {
        'test': test,
        'attempt': attempt,
        'part_groups': part_groups,
        'total_questions': total_gradable_slots(questions),
        'questions_range_display': _questions_range_display(questions, test=test),
        'saved_answers': saved_answers,
        'duration_minutes': test.duration_minutes or 60,
    }
    return render(request, 'mock_tests/take.html', context)


def test_result(request, pk, attempt_id):
    test = get_object_or_404(MockTest, pk=pk, is_active=True)
    session_key = _ensure_session(request)
    attempt = get_object_or_404(
        MockAttempt, pk=attempt_id, test=test, is_finished=True, session_key=session_key,
    )
    questions = list(test.questions.all())
    result = score_attempt(attempt, questions)

    context = {
        'test': test,
        'attempt': attempt,
        'result': result,
        'passed': result['passed'],
    }
    return render(request, 'mock_tests/result.html', context)
