"""IELTS-style javob normalizatsiyasi va solishtirish."""
import re

NUMBER_WORDS = {
    'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
    'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
    'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14',
    'fifteen': '15', 'sixteen': '16', 'seventeen': '17', 'eighteen': '18',
    'nineteen': '19', 'twenty': '20', 'thirty': '30', 'forty': '40', 'fifty': '50',
}

WORD_NUMBERS = {v: k for k, v in NUMBER_WORDS.items()}


def normalize_text(value):
    if value is None:
        return ''
    text = str(value).strip().lower()
    text = re.sub(r'\s+', ' ', text)
    return text


def _strip_punctuation(text):
    return re.sub(r"[^\w\s'-]", '', text)


def _strip_articles(text):
    return re.sub(r'^(?:a|an|the)\s+', '', text)


def _words_to_digits(text):
    out = text
    for word, digit in sorted(NUMBER_WORDS.items(), key=lambda x: -len(x[0])):
        out = re.sub(rf'\b{word}\b', digit, out)
    return out


def _digits_to_words(text):
    out = text
    for digit, word in WORD_NUMBERS.items():
        out = re.sub(rf'\b{digit}\b', word, out)
    return out


def expand_answer_variants(value):
    """Bitta javobning mumkin variantlari (IELTS tolerantligi)."""
    base = normalize_text(value)
    if not base:
        return set()

    variants = {base}
    clean = _strip_punctuation(base)
    variants.add(clean)

    no_article = _strip_articles(clean)
    variants.add(no_article)

    as_digits = _words_to_digits(clean)
    variants.add(as_digits)
    variants.add(_strip_articles(as_digits))

    as_words = _digits_to_words(clean)
    variants.add(as_words)
    variants.add(_strip_articles(as_words))

    return {v for v in variants if v}


def levenshtein(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[-1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def fuzzy_equal(a, b, max_distance=1):
    if not a or not b:
        return False
    if a == b:
        return True
    if abs(len(a) - len(b)) > max_distance:
        return False
    if min(len(a), len(b)) < 4:
        return False
    return levenshtein(a, b) <= max_distance


def match_text_answer(user_value, acceptable_values, allow_fuzzy=True):
    """Foydalanuvchi matni qabul qilinadigan javoblar ro'yxatiga mos keladimi."""
    user_variants = expand_answer_variants(user_value)
    if not user_variants:
        return False

    acceptable = []
    for item in acceptable_values or []:
        if item is None:
            continue
        s = str(item).strip()
        if s:
            acceptable.append(s)

    if not acceptable:
        return False

    for acc in acceptable:
        acc_variants = expand_answer_variants(acc)
        if user_variants & acc_variants:
            return True
        if allow_fuzzy:
            for u in user_variants:
                for a in acc_variants:
                    if fuzzy_equal(u, a):
                        return True
    return False


def collect_acceptable_answers(question):
    """Savol uchun barcha qabul qilinadigan matn javoblari."""
    acceptable = []
    raw = question.correct_answers_json
    if isinstance(raw, list):
        acceptable.extend(str(a) for a in raw if a is not None and str(a).strip())
    elif isinstance(raw, str) and raw.strip():
        acceptable.append(raw)
    if question.correct_answer and str(question.correct_answer).strip():
        acceptable.append(str(question.correct_answer))
    return acceptable


def normalize_choice(value):
    return normalize_text(value)


def count_words(text):
    t = (text or '').strip()
    if not t:
        return 0
    return len(t.split())


def score_extended_text(text, min_words=50, target_words=250):
    """Writing/Speaking: so'z soni bo'yicha 0..1 ball."""
    words = count_words(text)
    if words < min_words:
        return 0.0
    if words >= target_words:
        return 1.0
    span = max(target_words - min_words, 1)
    return round(0.5 + 0.5 * (words - min_words) / span, 4)
