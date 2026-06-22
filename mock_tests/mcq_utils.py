"""MCQ: A–H variantlar va ko'p tanlovli javoblar."""
import re

MCQ_LETTERS = 'abcdefgh'


def parse_mcq_options_lines(text):
    """Matn: a:Birinchi variant\\nb:Ikkinchi — ro'yxat."""
    if not text or not str(text).strip():
        return []
    options = []
    for line in str(text).splitlines():
        line = line.strip()
        if not line or ':' not in line:
            continue
        letter, _, label = line.partition(':')
        letter = letter.strip().lower()
        label = label.strip()
        if letter in MCQ_LETTERS and label:
            options.append({'letter': letter, 'text': label})
    return options


def parse_mcq_letters(value):
    """'a,c' yoki 'A C' -> ['a', 'c']."""
    if value is None:
        return []
    raw = str(value).strip().lower()
    if not raw:
        return []
    parts = re.split(r'[,;\s]+', raw)
    letters = []
    for part in parts:
        p = part.strip()
        if p and p in MCQ_LETTERS and p not in letters:
            letters.append(p)
    return sorted(letters)


def format_mcq_letters(letters):
    if isinstance(letters, (list, tuple)):
        parsed = [str(x).strip().lower() for x in letters if str(x).strip().lower() in MCQ_LETTERS]
        return ','.join(parsed)
    return ','.join(parse_mcq_letters(letters))


def get_mcq_correct_letters(question):
    """correct_answer yoki correct_answers_json dan to'g'ri harflar."""
    letters = parse_mcq_letters(question.correct_answer)
    if letters:
        return letters
    raw = question.correct_answers_json
    if isinstance(raw, list):
        if not raw:
            return []
        merged = []
        for item in raw:
            for letter in parse_mcq_letters(item):
                if letter not in merged:
                    merged.append(letter)
        return sorted(merged)
    if isinstance(raw, str):
        return parse_mcq_letters(raw)
    return []


def score_mcq(question, user_answer):
    """MCQ: (fraction 0..1, is_full, user_display, correct_display)."""
    correct = get_mcq_correct_letters(question)
    user = parse_mcq_letters(user_answer)
    select_count = question.get_mcq_select_count()
    correct_display = format_mcq_letters(correct) or '—'
    user_display = format_mcq_letters(user) or '—'

    if not correct:
        return 0.0, False, user_display, correct_display

    if select_count <= 1:
        ok = user == correct[:1] if len(correct) == 1 else user == correct
        return (1.0 if ok else 0.0), ok, user_display, correct_display

    correct_set = set(correct)
    got = len(correct_set & set(user))
    total = len(correct) or select_count
    frac = got / total if total else 0.0
    ok = user == correct and len(user) == select_count
    return frac, ok, user_display, correct_display
