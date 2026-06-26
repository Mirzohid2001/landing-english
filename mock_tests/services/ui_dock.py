"""Reading UI — dock raqamlari bilan savol yorliqlarini moslashtirish."""


def dock_map_from_part_groups(part_groups):
    dock = {}
    for group in part_groups:
        for btn in group['blank_buttons']:
            qid = btn['question_id']
            key = str(btn.get('blank_key') or '')
            dock.setdefault(qid, {})[key] = btn['num']
    return dock


def _sorted_nums(nums):
    return sorted(nums.values(), key=lambda x: int(x) if str(x).isdigit() else x)


def display_label_for_question(question, nums):
    if not nums:
        return question.get_order_display_label()
    if '' in nums and len(nums) == 1:
        return str(nums[''])
    if question.is_multi_answer_mcq():
        values = _sorted_nums({k: v for k, v in nums.items() if k != ''}) or _sorted_nums(nums)
        if len(values) > 1:
            return f'{values[0]}-{values[-1]}'
        if values:
            return str(values[0])
    if '' in nums:
        return str(nums[''])
    return question.get_order_display_label()


def attach_reading_ui_dock_labels(test, questions, part_groups):
    """Reading take sahifasi: kartadagi raqamlar dock bilan bir xil ketma-ket bo'ladi."""
    if test.test_type != 'reading':
        return
    dock = dock_map_from_part_groups(part_groups)
    for q in questions:
        nums = dock.get(q.pk, {})
        q.ui_dock_nums = nums
        q.ui_display_label = display_label_for_question(q, nums)

        for mf in getattr(q, 'ui_matching_fields', None) or []:
            key = str(mf['num'])
            mf['display_num'] = nums.get(key, mf['num'])

        rows = q.get_bracket_completion_rows()
        if rows:
            q.ui_bracket_rows = [
                {**row, 'display_num': nums.get(str(row['num']), row['num'])}
                for row in rows
            ]

        if q.question_type == 'summary_box':
            ui_lines = []
            for line in q.get_summary_lines():
                if line.get('spacer'):
                    ui_lines.append(line)
                    continue
                segs = []
                for seg in line.get('segments', []):
                    if seg.get('type') == 'blank':
                        key = str(seg['num'])
                        segs.append({**seg, 'display_num': nums.get(key, seg['num'])})
                    else:
                        segs.append(seg)
                ui_lines.append({**line, 'segments': segs})
            q.ui_summary_lines = ui_lines

        for seg in getattr(q, 'ui_bracket_segments', None) or []:
            if seg.get('type') == 'blank':
                key = str(seg['num'])
                seg['display_num'] = nums.get(key, seg['num'])

        if q.question_type in ('sentence_completion', 'summary_completion'):
            title, body = q.get_completion_title_body()
            q.ui_completion_title = title
            blank_values = [nums[k] for k in nums if k != '']
            if blank_values:
                sorted_vals = sorted(
                    blank_values, key=lambda x: int(x) if str(x).isdigit() else x,
                )
                q.ui_range_label = (
                    f'{sorted_vals[0]}-{sorted_vals[-1]}'
                    if len(sorted_vals) > 1 else str(sorted_vals[0])
                )
            parse_text = body if body else (q.question_text or '')
            inline_parts = []
            for part in q.parse_inline_parts(parse_text):
                if part.get('type') == 'input':
                    key = str(part['num'])
                    inline_parts.append({
                        **part,
                        'display_num': nums.get(key, part['num']),
                    })
                else:
                    inline_parts.append(part)
            if inline_parts:
                q.ui_reading_inline_parts = inline_parts
