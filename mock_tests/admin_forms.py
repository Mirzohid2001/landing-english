"""Admin: savol formasi — JSON o'rniga oddiy matn maydonlari."""
import json
import os
import re

from django import forms
from django.core.exceptions import ValidationError

from mock_tests.question_admin_helpers import (
    fix_misplaced_instruction,
    parse_fill_answers,
    sync_points_from_slots,
    validate_fill_type_fields,
)
from mock_tests.matching_utils import MATCHING_TYPES, parse_matching_correct, parse_matching_items, parse_matching_options
from mock_tests.mcq_utils import parse_mcq_letters, parse_mcq_options_lines
from mock_tests.models import MockPassage, MockQuestion

QUESTION_TYPE_RULES = {
    "mcq": "Variant A–H ni to'ldiring. «Tanlash soni» 2 bo'lsa — «To'g'ri javob»: a,c (vergul bilan).",
    "true_false_not_given": "Odatda A=True, B=False, C=Not Given. To'g'ri javob: a, b yoki c.",
    "yes_no_not_given": "Odatda A=Yes, B=No, C=Not Given. To'g'ri javob: a, b yoki c.",
    "fill_blank": "Savol matnida ______ yoki [1] ishlatishingiz mumkin. Qavs yo'q bo'lsa — vergul sinonimlar (9, nine). Qavs bo'lsa — har [N] uchun alohida javob.",
    "sentence_completion": "Bitta gap: ______ va bitta javob. Bir nechta gap: matnda [7], [8] — javoblar vergul bilan tartibda.",
    "summary_completion": "Matnda [1], [2] bo'lsa, javoblarni tartib bilan vergul bilan yozing.",
    "notes_completion": "Listening notes: matnda [1], [2]. Javoblar vergul bilan. Xarita uchun rasm — blokdagi birinchi savolga.",
    "table_completion": "Jadval: matnda [1], [2]. Jadval rasmi — blokdagi birinchi savolga yuklang.",
    "summary_box": "Savol matnida [1], [2]. Javoblar vergul bilan. So'zlar ro'yxati — har satrda bitta so'z.",
    "matching": "Eski: bitta tanlov — variantlar a|Matn, to'g'ri javob bitta harf.",
    "matching_headings": "Itemlar: 14|Paragraph A. Variantlar: i|Sarlavha. To'g'ri: 14:ii (har satr).",
    "matching_features": "Itemlar: 1|Ism. Variantlar: A|Matn. To'g'ri: 1:A",
    "matching_info": "Itemlar: 14|Savol matni. Variantlar: A|Paragraph A. To'g'ri: 14:A",
    "matching_sentences": "Itemlar + variantlar (A|ending). To'g'ri: 1:c",
    "classification": "Itemlar + A|B|C variantlar. To'g'ri: 1:A",
    "essay": "To'liq task matni. 50+ so'z yozilgan bo'lsa o'tadi.",
}


def question_type_rules_json():
    return json.dumps(QUESTION_TYPE_RULES, ensure_ascii=False)


ALLOWED_QUESTION_IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_QUESTION_IMAGE_BYTES = 5 * 1024 * 1024


class MockPassageAdminForm(forms.ModelForm):
    class Meta:
        model = MockPassage
        fields = "__all__"
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Masalan: Passage 1 — Part 1", "style": "width: 100%;"}
            ),
            "text": forms.Textarea(
                attrs={
                    "rows": 22,
                    "placeholder": "Passage to'liq matnini shu yerga yozing yoki nusxalang...",
                }
            ),
        }


class MockQuestionAdminForm(forms.ModelForm):
    fill_answers = forms.CharField(
        required=False,
        label="To'g'ri javoblar (vergul bilan)",
        help_text="Fill / summary / notes: marin, Marin yoki [1],[2] uchun tartib bilan",
        widget=forms.TextInput(attrs={"data-role": "qt-fill", "data-qt-field": "fill_answers"}),
    )
    matching_items = forms.CharField(
        required=False,
        label="Matching itemlar (savol bandlari)",
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "data-role": "qt-fill",
                "data-qt-field": "matching_items",
                "placeholder": "14|Paragraph A describes...\n15|Paragraph B explains...",
            }
        ),
        help_text="Har satr: raqam|Matn",
    )
    matching_options_lines = forms.CharField(
        required=False,
        label="Matching variantlar",
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "data-role": "qt-fill",
                "data-qt-field": "matching_options_lines",
                "placeholder": "Headings: i|Title one\nii|Title two\n\nFeatures: A|Name",
            }
        ),
        help_text="Headings: i|Sarlavha. Boshqalar: A|Matn",
    )
    matching_correct = forms.CharField(
        required=False,
        label="Matching to'g'ri javob",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "data-role": "qt-fill",
                "data-qt-field": "matching_correct",
                "placeholder": "14:ii\n15:v\n16:i",
            }
        ),
        help_text="Har satr: savol_raqami:variant (14:ii yoki 14: ii)",
    )
    word_list_lines = forms.CharField(
        required=False,
        label="Summary box — so'zlar ro'yxati",
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "data-role": "qt-fill",
                "data-qt-field": "word_list_lines",
            }
        ),
    )
    mcq_options_lines = forms.CharField(
        required=False,
        label="MCQ variantlar (ro'yxat — ixtiyoriy)",
        help_text="8 tadan ortiq yoki maxsus tartib: har satr a:Matn (a–h)",
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "data-role": "qt-mcq",
                "data-qt-field": "mcq_options_lines",
                "placeholder": "a:Birinchi variant\nb:Ikkinchi variant\nc:Uchinchi",
            }
        ),
    )
    mcq_select_count = forms.TypedChoiceField(
        required=False,
        label="Tanlash soni",
        choices=[(1, '1 ta javob'), (2, '2 ta javob'), (3, '3 ta javob')],
        coerce=int,
        initial=1,
        widget=forms.Select(attrs={"data-role": "qt-mcq", "data-qt-field": "mcq_select_count"}),
    )
    points = forms.IntegerField(
        min_value=1,
        label="Ball",
        help_text="Ko'p blank/matching slotlarida saqlashda avtomatik slot soniga tenglashtiriladi.",
        widget=forms.NumberInput(attrs={"data-qt-field": "points", "min": "1"}),
    )

    class Meta:
        model = MockQuestion
        fields = "__all__"
        widgets = {
            "question_text": forms.Textarea(attrs={"rows": 8}),
            "instruction": forms.Textarea(
                attrs={
                    "rows": 2,
                    "style": "width: 100%;",
                    "placeholder": "Qisqa ko'rsatma (summary matni emas!) — masalan: Choose NO MORE THAN ONE WORD...",
                }
            ),
            "option_a": forms.TextInput(attrs={"data-role": "qt-mcq"}),
            "option_b": forms.TextInput(attrs={"data-role": "qt-mcq"}),
            "option_c": forms.TextInput(attrs={"data-role": "qt-mcq"}),
            "option_d": forms.TextInput(attrs={"data-role": "qt-mcq"}),
            "option_e": forms.TextInput(attrs={"data-role": "qt-mcq"}),
            "option_f": forms.TextInput(attrs={"data-role": "qt-mcq"}),
            "option_g": forms.TextInput(attrs={"data-role": "qt-mcq"}),
            "option_h": forms.TextInput(attrs={"data-role": "qt-mcq"}),
            "correct_answer": forms.TextInput(
                attrs={"data-role": "qt-mcq", "placeholder": "a yoki a,c"}
            ),
            "audio_timestamp": forms.NumberInput(attrs={"step": "0.1", "min": "0", "data-qt-field": "audio_timestamp"}),
            "image": forms.ClearableFileInput(attrs={"data-qt-field": "image", "accept": "image/jpeg,image/png,image/gif,image/webp"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        inst = self.instance
        if inst and inst.pk:
            answers = inst.correct_answers_json
            if isinstance(answers, list) and answers:
                self.fields["fill_answers"].initial = ", ".join(str(a) for a in answers)
            elif isinstance(answers, dict) and answers:
                lines = [f"{k}:{v}" for k, v in sorted(
                    answers.items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else str(x[0])
                )]
                self.fields["matching_correct"].initial = "\n".join(lines)
            opts = inst.options_json or {}
            if isinstance(opts, dict):
                items = opts.get("items", [])
                if items:
                    item_lines = []
                    for it in items:
                        if isinstance(it, dict):
                            item_lines.append(f"{it.get('num', '')}|{it.get('label', '')}")
                    self.fields["matching_items"].initial = "\n".join(item_lines)
                headings = opts.get("headings", [])
                options = headings or opts.get("options", [])
                if options and inst.question_type != 'mcq':
                    lines = []
                    for item in options:
                        if isinstance(item, dict):
                            letter = (item.get("letter") or "").strip()
                            text = (item.get("text") or "").strip()
                            if letter:
                                lines.append(f"{letter}|{text}")
                    self.fields["matching_options_lines"].initial = "\n".join(lines)
                mcq_opts = opts.get("mcq_options", [])
                if mcq_opts:
                    self.fields["mcq_options_lines"].initial = "\n".join(
                        f"{o.get('letter', '')}:{o.get('text', '')}" for o in mcq_opts if isinstance(o, dict)
                    )
                if opts.get("word_list"):
                    self.fields["word_list_lines"].initial = "\n".join(str(w) for w in opts["word_list"])
            if inst.mcq_select_count:
                self.fields["mcq_select_count"].initial = inst.mcq_select_count
            slots = max(1, inst.gradable_slot_count())
            self.fields["points"].help_text = (
                f"Baholanadigan slotlar: {slots}. "
                "Saqlashda ball avtomatik shu songa tenglashtiriladi."
            )

    def clean_correct_answers_json(self):
        value = self.cleaned_data.get("correct_answers_json")
        if value in (None, ""):
            return []
        if isinstance(value, (list, dict)):
            return value
        raise ValidationError("correct_answers_json list yoki dict bo'lishi kerak.")

    def clean_options_json(self):
        value = self.cleaned_data.get("options_json", {})
        if value in (None, ""):
            return {}
        if not isinstance(value, dict):
            raise ValidationError("options_json obyekt (dict) bo'lishi kerak.")
        return value

    @staticmethod
    def _parse_fill_answers(text):
        return parse_fill_answers(text)

    @staticmethod
    def _parse_word_list(text):
        return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            return image
        if hasattr(image, 'size') and image.size > MAX_QUESTION_IMAGE_BYTES:
            raise ValidationError('Rasm hajmi 5 MB dan oshmasin.')
        ext = os.path.splitext(getattr(image, 'name', '') or '')[1].lower()
        if ext and ext not in ALLOWED_QUESTION_IMAGE_EXT:
            raise ValidationError('Faqat JPG, PNG, GIF yoki WEBP formatlari qabul qilinadi.')
        return image

    def clean(self):
        cleaned = super().clean()
        qtype = cleaned.get("question_type") or "mcq"
        fill_text = (cleaned.get("fill_answers") or "").strip()
        items_text = (cleaned.get("matching_items") or "").strip()
        match_opts = (cleaned.get("matching_options_lines") or "").strip()
        match_corr = (cleaned.get("matching_correct") or "").strip()
        word_lines = (cleaned.get("word_list_lines") or "").strip()
        has_text = bool((cleaned.get("question_text") or "").strip())
        options_json = dict(cleaned.get("options_json") or {})

        fill_types = (
            "fill_blank", "sentence_completion", "summary_completion",
            "summary_box", "notes_completion", "table_completion",
        )
        if qtype in fill_types and fill_text:
            cleaned["correct_answers_json"] = self._parse_fill_answers(fill_text)
            if cleaned["correct_answers_json"] and not cleaned.get("correct_answer"):
                cleaned["correct_answer"] = cleaned["correct_answers_json"][0]

        fill_errors = validate_fill_type_fields(
            qtype,
            cleaned.get("question_text") or "",
            fill_text,
        )
        if fill_errors:
            raise ValidationError(fill_errors)

        if qtype == "matching" and match_opts:
            options_json["options"] = parse_matching_options(match_opts)
            cleaned["options_json"] = options_json

        if qtype in MATCHING_TYPES and (items_text or match_opts or match_corr):
            items = parse_matching_items(items_text)
            headings_mode = qtype == "matching_headings"
            headings = parse_matching_options(match_opts, headings_mode=headings_mode)
            corr_map = parse_matching_correct(match_corr)
            if items:
                options_json["items"] = items
            if headings:
                if headings_mode:
                    options_json["headings"] = headings
                options_json["options"] = headings
            if corr_map:
                cleaned["correct_answers_json"] = corr_map
            cleaned["options_json"] = options_json
            if has_text and (not items or not corr_map):
                raise ValidationError(
                    "Matching: «Matching itemlar» va «Matching to'g'ri javob» (14:ii) to'ldiring."
                )
            if has_text and qtype == "matching_headings" and not headings:
                raise ValidationError(
                    "Matching Headings: variantlar — i|Sarlavha, ii|Boshqa..."
                )

        if qtype == "summary_box" and word_lines:
            options_json["word_list"] = self._parse_word_list(word_lines)
            cleaned["options_json"] = options_json

        if qtype == "summary_box":
            instr = (cleaned.get("instruction") or "").strip()
            qtext = (cleaned.get("question_text") or "").strip()
            if instr and re.search(r"\[\d+\]", instr):
                raise ValidationError({
                    "instruction": (
                        "Ko'rsatma qisqa bo'lishi kerak. Summary matnini "
                        "'Savol matni' maydoniga yozing ([11] kabi qavslar u yerda)."
                    ),
                })
            if instr and qtext and " ".join(instr.split()) == " ".join(qtext.split()):
                raise ValidationError({
                    "instruction": "Ko'rsatma va savol matni bir xil bo'lmasligi kerak.",
                })

        mcq_types = ("mcq", "true_false_not_given", "yes_no_not_given")
        if has_text and qtype == "matching" and not cleaned.get("correct_answer"):
            raise ValidationError({"correct_answer": "Eski matching: bitta harf kiriting."})
        if has_text and qtype in mcq_types and not cleaned.get("correct_answer"):
            raise ValidationError({"correct_answer": "To'g'ri javob (harf) kiriting."})

        if has_text and qtype == "mcq":
            select_count = int(cleaned.get("mcq_select_count") or 1)
            select_count = max(1, min(select_count, 3))
            cleaned["mcq_select_count"] = select_count
            correct_letters = parse_mcq_letters(cleaned.get("correct_answer", ""))
            if len(correct_letters) != select_count:
                raise ValidationError({
                    "correct_answer": (
                        f"Tanlash soni {select_count} — {select_count} ta harf kiriting "
                        f"(masalan: {'a,c' if select_count == 2 else 'a'})"
                    ),
                })
            mcq_lines = (cleaned.get("mcq_options_lines") or "").strip()
            field_options = [
                cleaned.get(f"option_{letter}") for letter in "abcdefgh"
            ]
            has_options = any(str(v or "").strip() for v in field_options)
            if mcq_lines:
                parsed = parse_mcq_options_lines(mcq_lines)
                if not parsed:
                    raise ValidationError({"mcq_options_lines": "Format: a:Matn (har satr)"})
                options_json = dict(cleaned.get("options_json") or {})
                options_json["mcq_options"] = parsed
                cleaned["options_json"] = options_json
            elif not has_options:
                raise ValidationError("Kamida bitta variant (A–H) yoki MCQ ro'yxatini to'ldiring.")
            elif len([v for v in field_options if str(v or "").strip()]) < select_count + 1:
                raise ValidationError(
                    f"Kamida {select_count + 1} ta variant kerak ({select_count} ta javob tanlanadi)."
                )

        test = cleaned.get("test") or getattr(self.instance, "test", None)
        if test and test.test_type == "reading" and qtype in ("notes_completion", "table_completion"):
            raise ValidationError("Notes/Table faqat Listening test uchun.")

        if cleaned.get("image") and test and test.test_type != "listening":
            raise ValidationError({"image": "Rasm faqat Listening test savollariga biriktiriladi."})

        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        qtype = obj.question_type
        fill_text = self.cleaned_data.get("fill_answers", "")
        if qtype in (
            "fill_blank", "sentence_completion", "summary_completion",
            "summary_box", "notes_completion", "table_completion",
        ) and fill_text:
            obj.correct_answers_json = self._parse_fill_answers(fill_text)

        items_text = self.cleaned_data.get("matching_items", "")
        match_opts = self.cleaned_data.get("matching_options_lines", "")
        match_corr = self.cleaned_data.get("matching_correct", "")
        if qtype == "matching" and match_opts:
            opts = dict(obj.options_json or {})
            opts["options"] = parse_matching_options(match_opts)
            obj.options_json = opts
        if qtype in MATCHING_TYPES:
            opts = dict(obj.options_json or {})
            if items_text:
                opts["items"] = parse_matching_items(items_text)
            if match_opts:
                headings = parse_matching_options(match_opts, headings_mode=(qtype == "matching_headings"))
                if qtype == "matching_headings":
                    opts["headings"] = headings
                opts["options"] = headings
            if match_corr:
                obj.correct_answers_json = parse_matching_correct(match_corr)
            obj.options_json = opts

        word_lines = self.cleaned_data.get("word_list_lines", "")
        if qtype == "summary_box" and word_lines:
            opts = dict(obj.options_json or {})
            opts["word_list"] = self._parse_word_list(word_lines)
            obj.options_json = opts

        if qtype == "mcq":
            mcq_lines = (self.cleaned_data.get("mcq_options_lines") or "").strip()
            opts = dict(obj.options_json or {})
            if mcq_lines:
                opts["mcq_options"] = parse_mcq_options_lines(mcq_lines)
            else:
                opts.pop("mcq_options", None)
            obj.options_json = opts
            select = self.cleaned_data.get("mcq_select_count")
            if select:
                obj.mcq_select_count = int(select)

        fix_misplaced_instruction(obj)
        sync_points_from_slots(obj)

        if commit:
            obj.save()
            self.save_m2m()
        return obj
