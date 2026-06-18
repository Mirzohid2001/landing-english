"""Admin: savol formasi — JSON o'rniga oddiy matn maydonlari."""
import json
import re

from django import forms
from django.core.exceptions import ValidationError

from mock_tests.matching_utils import MATCHING_TYPES, parse_matching_correct, parse_matching_items, parse_matching_options
from mock_tests.models import MockPassage, MockQuestion

QUESTION_TYPE_RULES = {
    "mcq": "Variant A–D ni to'ldiring. «To'g'ri javob» da bitta harf: a, b, c yoki d.",
    "true_false_not_given": "Odatda A=True, B=False, C=Not Given. To'g'ri javob: a, b yoki c.",
    "yes_no_not_given": "Odatda A=Yes, B=No, C=Not Given. To'g'ri javob: a, b yoki c.",
    "fill_blank": "Savol matnida ______ yoki [1] ishlatishingiz mumkin. «To'g'ri javoblar» — vergul bilan.",
    "sentence_completion": "Bitta yoki bir nechta to'g'ri javob — vergul bilan.",
    "summary_completion": "Matnda [1], [2] bo'lsa, javoblarni tartib bilan vergul bilan yozing.",
    "notes_completion": "Listening notes: matnda [1], [2]. Javoblar vergul bilan. Audio vaqti (soniya) kiriting.",
    "table_completion": "Jadval: matnda [1], [2]. Javoblar vergul bilan.",
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

    class Meta:
        model = MockQuestion
        fields = "__all__"
        widgets = {
            "question_text": forms.Textarea(attrs={"rows": 8}),
            "instruction": forms.TextInput(attrs={"style": "width: 100%;"}),
            "option_a": forms.TextInput(attrs={"data-role": "qt-mcq"}),
            "option_b": forms.TextInput(attrs={"data-role": "qt-mcq"}),
            "option_c": forms.TextInput(attrs={"data-role": "qt-mcq"}),
            "option_d": forms.TextInput(attrs={"data-role": "qt-mcq"}),
            "correct_answer": forms.TextInput(attrs={"data-role": "qt-mcq"}),
            "audio_timestamp": forms.NumberInput(attrs={"step": "0.1", "min": "0", "data-qt-field": "audio_timestamp"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        inst = self.instance
        if not inst or not inst.pk:
            return
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
            if options:
                lines = []
                for item in options:
                    if isinstance(item, dict):
                        letter = (item.get("letter") or "").strip()
                        text = (item.get("text") or "").strip()
                        if letter:
                            lines.append(f"{letter}|{text}")
                self.fields["matching_options_lines"].initial = "\n".join(lines)
            if opts.get("word_list"):
                self.fields["word_list_lines"].initial = "\n".join(str(w) for w in opts["word_list"])

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
        if not text or not str(text).strip():
            return []
        return [p.strip() for p in str(text).replace("\n", ",").split(",") if p.strip()]

    @staticmethod
    def _parse_word_list(text):
        return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]

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

        mcq_types = ("mcq", "true_false_not_given", "yes_no_not_given")
        if has_text and qtype == "matching" and not cleaned.get("correct_answer"):
            raise ValidationError({"correct_answer": "Eski matching: bitta harf kiriting."})
        if has_text and qtype in mcq_types and not cleaned.get("correct_answer"):
            raise ValidationError({"correct_answer": "To'g'ri javob (harf) kiriting."})

        bracket_types = (
            "summary_completion", "summary_box", "notes_completion", "table_completion",
        )
        if has_text and qtype in bracket_types:
            qtext = cleaned.get("question_text") or ""
            brackets = re.findall(r"\[(\d+)\]", qtext)
            if not brackets:
                raise ValidationError({
                    "question_text": "Matnda kamida bitta [1] ko'rinishi kerak.",
                })
            answers = cleaned.get("correct_answers_json")
            if not answers and fill_text:
                answers = self._parse_fill_answers(fill_text)
            if not answers:
                raise ValidationError({
                    "fill_answers": "Bracket soniga mos javoblarni vergul bilan kiriting.",
                })
            if len(answers) != len(brackets):
                raise ValidationError({
                    "fill_answers": (
                        f"Javoblar soni ({len(answers)}) bracket soni "
                        f"({len(brackets)}) bilan mos kelishi kerak."
                    ),
                })

        test = cleaned.get("test") or getattr(self.instance, "test", None)
        if test and test.test_type == "reading" and qtype in ("notes_completion", "table_completion"):
            raise ValidationError("Notes/Table faqat Listening test uchun.")

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

        if commit:
            obj.save()
            self.save_m2m()
        return obj
