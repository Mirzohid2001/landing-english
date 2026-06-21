"""Admin: savol maydonlarini avtomatik tuzatish va ball sinxronlash."""
import re

BRACKET_IN_TEXT = re.compile(r'\[\d+\]')
BRACKET_SLOT = re.compile(r'\[\d+\]')

FILL_MULTI_TYPES = (
    'summary_box',
    'notes_completion',
    'table_completion',
    'sentence_completion',
    'summary_completion',
)

MULTI_MATCHING_TYPES = (
    'matching_headings',
    'matching_features',
    'matching_info',
    'matching_sentences',
    'classification',
)


def count_bracket_slots(text):
    return len(BRACKET_SLOT.findall(text or ''))


def count_comma_answers(text):
    if not (text or '').strip():
        return 0
    return len([part for part in text.replace('\n', ',').split(',') if part.strip()])


def estimate_gradable_slots(
    question_type,
    question_text='',
    fill_answers='',
    matching_correct='',
    matching_items='',
):
    """Admin JS `estimateGradableSlots` bilan bir xil mantiq."""
    brackets = count_bracket_slots(question_text)
    if question_type in FILL_MULTI_TYPES:
        if brackets:
            return max(1, brackets)
        comma = count_comma_answers(fill_answers)
        if comma:
            return comma
        return 1
    if question_type in MULTI_MATCHING_TYPES:
        corr_lines = [line for line in (matching_correct or '').split('\n') if line.strip()]
        if corr_lines:
            return len(corr_lines)
        item_lines = [line for line in (matching_items or '').split('\n') if line.strip()]
        return max(1, len(item_lines))
    return 1


def instruction_looks_like_question_body(text):
    """Ko'rsatma maydoniga noto'g'ri qo'yilgan summary/sentence matnimi."""
    text = (text or '').strip()
    if not text:
        return False
    if BRACKET_IN_TEXT.search(text):
        return True
    if '\n' in text:
        return True
    if text.count('--') >= 2:
        return True
    return len(text) > 220


def fix_misplaced_instruction(question):
    """
    Summary/sentence matni ko'rsatma maydonida bo'lsa — savol matniga ko'chirish.
    True qaytarsa maydonlar o'zgardi.
    """
    if question.question_type not in ('summary_box', 'sentence_completion', 'summary_completion'):
        return False

    instr = (question.instruction or '').strip()
    qtext = (question.question_text or '').strip()
    if not instr:
        return False

    norm_instr = ' '.join(instr.split())
    norm_qtext = ' '.join(qtext.split())
    if norm_qtext and norm_instr == norm_qtext:
        question.instruction = ''
        return True

    if not instruction_looks_like_question_body(instr):
        return False

    if not qtext:
        question.question_text = instr
        question.instruction = ''
        return True

    if BRACKET_IN_TEXT.search(qtext) or len(qtext) > 40:
        question.instruction = ''
        return True

    question.question_text = instr
    question.instruction = qtext
    return True


def sync_points_from_slots(question):
    """Ball maydonini baholanadigan slotlar soniga tenglashtirish."""
    slots = max(1, question.gradable_slot_count())
    if question.points != slots:
        question.points = slots
        return True
    return False


def sanitize_block_instruction(instruction, questions):
    """Frontend ko'rsatma bloki — summary matnini qayta ko'rsatmaslik."""
    text = (instruction or '').strip()
    if not text:
        return ''
    summary_qs = [q for q in questions if q.question_type == 'summary_box']
    if not summary_qs:
        return text
    if instruction_looks_like_question_body(text):
        return ''
    normalized = ' '.join(text.split())
    for q in summary_qs:
        qtext = ' '.join((q.question_text or '').split())
        if qtext and normalized == qtext:
            return ''
    return text
