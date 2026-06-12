"""Matching savollar uchun yordamchi funksiyalar."""
import json
import re


MATCHING_TYPES = (
    'matching_headings',
    'matching_features',
    'matching_info',
    'matching_sentences',
    'classification',
)

LEGACY_MATCHING = 'matching'


def is_matching_type(qtype):
    return qtype in MATCHING_TYPES or qtype == LEGACY_MATCHING


def is_multi_matching_type(qtype):
    return qtype in MATCHING_TYPES


def parse_user_matching_answer(user_answer):
    if not user_answer:
        return {}
    if isinstance(user_answer, dict):
        return {str(k): str(v).strip() for k, v in user_answer.items()}
    text = str(user_answer).strip()
    if text.startswith('{'):
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return {str(k): str(v).strip() for k, v in data.items()}
        except json.JSONDecodeError:
            pass
    return {}


def normalize_match_value(value):
    if value is None:
        return ''
    return str(value).strip().lower()


def build_matching_fields(question, user_answer=None):
    """Take sahifasi uchun dropdown qatorlari."""
    qtype = question.question_type
    if not is_multi_matching_type(qtype):
        return []

    opts = question.options_json or {}
    correct = question.correct_answers_json if isinstance(question.correct_answers_json, dict) else {}
    items = opts.get('items', opts.get('paragraphs', []))
    if not items and correct:
        items = [
            {'num': k, 'label': f'Item {k}'}
            for k in sorted(correct.keys(), key=lambda x: int(x) if str(x).isdigit() else str(x))
        ]

    if qtype == 'matching_headings':
        options = opts.get('headings', []) or opts.get('options', [])
    else:
        options = opts.get('options', []) or opts.get('headings', [])

    if not options and correct:
        letters = sorted({str(v) for v in correct.values()})
        options = [{'letter': letter, 'text': letter} for letter in letters]

    cur = parse_user_matching_answer(user_answer)
    fields = []
    opts_list = options if isinstance(options, list) else []
    for i, it in enumerate(items):
        if isinstance(it, dict):
            num = it.get('num', i + 1)
            label = it.get('label', '')
        else:
            num, label = i + 1, str(it)
        fields.append({
            'num': num,
            'label': label,
            'value': cur.get(str(num), ''),
            'options': [
                {
                    'letter': (o.get('letter', o) if isinstance(o, dict) else o),
                    'text': (o.get('text', '') if isinstance(o, dict) else str(o)),
                }
                for o in opts_list
            ],
        })
    return fields


def get_matching_ref_options(question):
    """Tepada ko'rsatiladigan variantlar ro'yxati."""
    qtype = question.question_type
    if not is_multi_matching_type(qtype):
        return []
    if qtype == 'matching_info':
        return []
    opts = question.options_json or {}
    if qtype == 'matching_headings':
        options = opts.get('headings', []) or opts.get('options', [])
    else:
        options = opts.get('options', []) or opts.get('headings', [])
    return options if isinstance(options, list) else []


def matching_ref_title(qtype):
    titles = {
        'matching_headings': 'List of Headings',
        'matching_features': 'List of people / features',
        'matching_sentences': 'Sentence endings',
        'matching_info': 'Paragraphs',
        'classification': 'Categories',
    }
    return titles.get(qtype, 'Options')


def parse_matching_items(text):
    items = []
    for idx, line in enumerate([ln.strip() for ln in (text or '').splitlines() if ln.strip()]):
        if '|' in line:
            left, right = line.split('|', 1)
            left, right = left.strip(), right.strip()
            num = int(left) if left.isdigit() else (idx + 1)
            items.append({'num': num, 'label': right})
        else:
            m = re.match(r'^(\d+)\s+(.+)$', line)
            if m:
                num = int(m.group(1))
                if num >= 20:
                    num = int(str(num)[0])
                items.append({'num': num, 'label': m.group(2).strip()})
            else:
                items.append({'num': idx + 1, 'label': line})
    return items


def parse_matching_options(text, headings_mode=False):
    options = []
    for line in [ln.strip() for ln in (text or '').splitlines() if ln.strip()]:
        if '|' in line:
            letter, body = line.split('|', 1)
            options.append({'letter': letter.strip().lower(), 'text': body.strip()})
        else:
            if headings_mode:
                mrom = re.match(r'^([ivxlcdm]+)\s*[.):\-]?\s*(.*)$', line, re.I)
                if mrom and mrom.group(1):
                    options.append({'letter': mrom.group(1).lower(), 'text': (mrom.group(2) or '').strip()})
                    continue
            parts = line.split(None, 1)
            tok = parts[0] if parts else ''
            if len(tok) == 1 and tok.isalpha():
                options.append({'letter': tok.lower(), 'text': (parts[1] if len(parts) > 1 else '').strip()})
    return options


def parse_matching_correct(text):
    corr_map = {}
    for line in [ln.strip() for ln in (text or '').splitlines() if ln.strip()]:
        if ':' in line:
            k, v = line.split(':', 1)
            corr_map[k.strip()] = v.strip().lower()
        else:
            m = re.match(r'^(\d+)\s+(.+)$', line)
            if m:
                corr_map[m.group(1).strip()] = m.group(2).strip().lower()
    return corr_map
