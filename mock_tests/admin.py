import json
import tempfile
from pathlib import Path

from django.contrib import admin, messages
from django.core.management import call_command
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .admin_forms import (
    MockPassageAdminForm,
    MockQuestionAdminForm,
    question_type_rules_json,
)
from .models import MockAttempt, MockPassage, MockQuestion, MockTest
from .question_admin_helpers import fix_misplaced_instruction, sync_points_from_slots


class MockPassageInline(admin.StackedInline):
    model = MockPassage
    form = MockPassageAdminForm
    extra = 0
    min_num = 0
    ordering = ["order", "pk"]
    show_change_link = True
    classes = []
    verbose_name = "Passage"
    verbose_name_plural = "Passage'lar (faqat Reading — Part 1, 2, 3)"
    fields = ["order", "title", "text"]


class MockQuestionInline(admin.StackedInline):
    model = MockQuestion
    form = MockQuestionAdminForm
    extra = 1
    min_num = 0
    ordering = ["order", "pk"]
    show_change_link = True
    classes = []

    class Media:
        js = ("admin/mock_tests/question_admin.js",)
        css = {"all": ("admin/mock_tests/question_admin.css",)}
    verbose_name = "Savol"
    verbose_name_plural = "Savollar — tez shablon yoki «Yana bir Savol qo'shish»"

    def get_fieldsets(self, request, obj=None):
        return QUESTION_FIELDSETS


QUESTION_FIELDSETS = [
    (
        None,
        {
            "fields": [
                ("order", "part_number", "question_type", "points"),
                "instruction",
                "question_text",
                "image",
            ],
        },
    ),
    (
        "Variantlar (MCQ — A dan H gacha)",
        {
            "fields": [
                "mcq_select_count",
                ("option_a", "option_b"),
                ("option_c", "option_d"),
                ("option_e", "option_f"),
                ("option_g", "option_h"),
                "mcq_options_lines",
                "correct_answer",
            ],
            "classes": ["question-mcq-fields"],
        },
    ),
    (
        "To'ldirish / Matching / Summary box",
        {
            "fields": [
                "fill_answers",
                "matching_items",
                "matching_options_lines",
                "matching_correct",
                "word_list_lines",
                "audio_timestamp",
                "explanation",
            ],
            "classes": ["question-fill-fields"],
        },
    ),
    (
        "Qo'shimcha (JSON / audio)",
        {
            "classes": ["collapse"],
            "fields": ["correct_answers_json", "options_json"],
        },
    ),
]


@admin.register(MockTest)
class MockTestAdmin(admin.ModelAdmin):
    change_form_template = "admin/mock_tests/change_form.html"
    change_list_template = "admin/mock_tests/change_list.html"
    view_on_site = True
    list_display = [
        "title",
        "test_type",
        "difficulty",
        "content_summary_display",
        "attempts_count",
        "is_active",
        "updated_at",
    ]
    list_filter = ["test_type", "difficulty", "is_active", "created_at"]
    search_fields = ["title", "description"]
    list_editable = ["is_active"]
    ordering = ["-updated_at", "-created_at"]
    readonly_fields = []
    save_as = True
    save_on_top = True
    list_per_page = 25
    actions = ["duplicate_tests", "activate_tests", "deactivate_tests", "fix_test_questions"]

    class Media:
        js = ("admin/mock_tests/question_admin.js",)
        css = {"all": ("admin/mock_tests/question_admin.css",)}

    def get_fieldsets(self, request, obj=None):
        fs = [
            (
                "Asosiy ma'lumotlar",
                {
                    "fields": ("title", "test_type", "difficulty", "description", "is_active"),
                    "description": (
                        "<strong>1-qadam:</strong> maydonlarni to'ldirib <strong>Saqlash</strong> — "
                        "keyin pastda Passage va Savollar paydo bo'ladi. "
                        "Yangi savol qatorida <strong>order</strong> va <strong>part</strong> avtomatik to'ldiriladi. "
                        "«Oldingisidan nusxa» tugmasi bilan o'xshash savolni tez qo'shing."
                    ),
                },
            ),
            (
                "Parametrlar",
                {
                    "fields": ("duration_minutes", "passing_score", "audio_file"),
                    "description": "Listening uchun audio fayl yuklang.",
                },
            ),
        ]
        if obj:
            fs.append(
                (
                    "Ko'rinish",
                    {
                        "fields": (
                            "preview_link",
                            "content_summary_display",
                            "created_at",
                            "updated_at",
                        ),
                    },
                )
            )
        return fs

    def get_inlines(self, request, obj):
        if obj and obj.test_type != "reading":
            return [MockQuestionInline]
        return [MockPassageInline, MockQuestionInline]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [
                "preview_link",
                "content_summary_display",
                "created_at",
                "updated_at",
            ]
        return []

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "stats/",
                self.admin_site.admin_view(self.stats_view),
                name="mock_tests_mocktest_stats",
            ),
            path(
                "import-json/",
                self.admin_site.admin_view(self.import_json_view),
                name="mock_tests_mocktest_import_json",
            ),
        ]
        return custom + urls

    def stats_view(self, request):
        days = int(request.GET.get("days", 7))
        days = max(1, min(days, 90))
        context = {
            **self.admin_site.each_context(request),
            "title": "Mock test statistikasi",
            "opts": self.model._meta,
            "stats": get_dashboard_stats(days=days),
        }
        return render(request, "admin/mock_tests/stats.html", context)

    def import_json_view(self, request):
        if request.method == "POST":
            upload = request.FILES.get("json_file")
            update = request.POST.get("update") == "on"
            if not upload:
                messages.error(request, "JSON fayl tanlang.")
            else:
                try:
                    data = json.loads(upload.read().decode("utf-8"))
                    title = data.get("title", "import")
                    suffix = Path(upload.name).suffix or ".json"
                    with tempfile.NamedTemporaryFile(
                        mode="w",
                        suffix=suffix,
                        delete=False,
                        encoding="utf-8",
                    ) as tmp:
                        json.dump(data, tmp, ensure_ascii=False)
                        tmp_path = tmp.name
                    call_command(
                        "import_mock_test",
                        tmp_path,
                        update=update,
                        verbosity=0,
                    )
                    test = MockTest.objects.filter(title=title).first()
                    if test:
                        messages.success(
                            request,
                            f'"{test.title}" import qilindi — {test.questions.count()} savol.',
                        )
                        return redirect(
                            reverse(
                                "admin:mock_tests_mocktest_change",
                                args=[test.pk],
                            )
                        )
                    messages.success(request, "Import bajarildi.")
                    return redirect("admin:mock_tests_mocktest_changelist")
                except json.JSONDecodeError:
                    messages.error(request, "JSON formati noto'g'ri.")
                except Exception as exc:
                    messages.error(request, f"Import xatolik: {exc}")

        context = {
            **self.admin_site.each_context(request),
            "title": "JSON dan test import",
            "opts": self.model._meta,
            "import_url": reverse("admin:mock_tests_mocktest_import_json"),
            "sample_path": "mock_tests/fixtures/sample_import_test.json",
        }
        return render(request, "admin/mock_tests/import_json.html", context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["question_type_rules_json"] = question_type_rules_json()
        extra_context["import_json_url"] = reverse(
            "admin:mock_tests_mocktest_import_json"
        )
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )

    def add_view(self, request, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["question_type_rules_json"] = question_type_rules_json()
        extra_context["import_json_url"] = reverse(
            "admin:mock_tests_mocktest_import_json"
        )
        return super().add_view(request, form_url, extra_context=extra_context)

    def preview_link(self, obj):
        if not obj or not obj.pk:
            return "—"
        url = obj.get_absolute_url()
        return format_html('<a href="{}" target="_blank">Saytda ko\'rish</a>', url)

    preview_link.short_description = "Sayt"

    def content_summary_display(self, obj):
        if not obj or not obj.pk:
            return "—"
        p_count = obj.passages.count()
        slot_count = obj.total_questions
        if obj.test_type == "reading" and p_count:
            return format_html("{} passage / {} slot", p_count, slot_count)
        return format_html("<strong>{}</strong> slot", slot_count)

    content_summary_display.short_description = "Tarkib"

    def attempts_count(self, obj):
        if not obj or not obj.pk:
            return 0
        return obj.attempts.count()

    attempts_count.short_description = "Urinishlar"

    @admin.action(description="Testni nusxalash (passage + savollar)")
    def duplicate_tests(self, request, queryset):
        n = 0
        for old in queryset:
            questions = list(old.questions.all().order_by("order", "pk"))
            passages = list(old.passages.all().order_by("order", "pk"))
            with transaction.atomic():
                old.pk = None
                old._state.adding = True
                old.title = f"{old.title} (nusxa)"
                old.save()
                for p in passages:
                    p.pk = None
                    p.test = old
                    p._state.adding = True
                    p.save()
                for q in questions:
                    q.pk = None
                    q.test = old
                    q._state.adding = True
                    q.save()
            n += 1
        self.message_user(
            request, f"{n} ta test nusxalandi.", messages.SUCCESS
        )

    @admin.action(description="Savollarni tuzatish (ball + ko'rsatma)")
    def fix_test_questions(self, request, queryset):
        instr_fixed = 0
        points_fixed = 0
        for test in queryset:
            for q in test.questions.all():
                if fix_misplaced_instruction(q):
                    instr_fixed += 1
                if sync_points_from_slots(q):
                    points_fixed += 1
                q.save(update_fields=['instruction', 'question_text', 'points'])
        self.message_user(
            request,
            f"Ko'rsatma: {instr_fixed} ta, ball: {points_fixed} ta savol yangilandi.",
            messages.SUCCESS,
        )

    @admin.action(description="Faollashtirish")
    def activate_tests(self, request, queryset):
        n = queryset.update(is_active=True)
        self.message_user(request, f"{n} ta test faollashtirildi.")

    @admin.action(description="Faol emas qilish")
    def deactivate_tests(self, request, queryset):
        n = queryset.update(is_active=False)
        self.message_user(request, f"{n} ta test o'chirildi.")


@admin.register(MockQuestion)
class MockQuestionAdmin(admin.ModelAdmin):
    form = MockQuestionAdminForm
    list_display = [
        "test",
        "order",
        "part_number",
        "question_type",
        "question_text_short",
        "correct_answer",
        "points",
    ]
    list_filter = [
        "test__test_type",
        "test__is_active",
        "question_type",
        "part_number",
    ]
    search_fields = ["question_text", "test__title", "instruction"]
    ordering = ["test", "order", "pk"]
    autocomplete_fields = ["test"]
    list_select_related = ["test"]
    save_as = True
    save_on_top = True
    list_per_page = 40
    actions = ["duplicate_questions"]

    class Media:
        js = ("admin/mock_tests/question_admin.js",)
        css = {"all": ("admin/mock_tests/question_admin.css",)}

    def get_fieldsets(self, request, obj=None):
        fieldsets = [("Test", {"fields": ["test"]})]
        for i, (title, opts) in enumerate(QUESTION_FIELDSETS):
            if i == 0:
                fields = list(opts["fields"])
                if obj and obj.image:
                    fields = fields + ["image_preview"]
                fieldsets.append((title, {**opts, "fields": fields}))
            else:
                fieldsets.append((title, opts))
        return fieldsets

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["question_type_rules_json"] = question_type_rules_json()
        obj = self.get_object(request, object_id)
        if obj and obj.test_id:
            extra_context["mock_question_test_type"] = obj.test.test_type
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )

    def add_view(self, request, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["question_type_rules_json"] = question_type_rules_json()
        return super().add_view(request, form_url, extra_context=extra_context)

    def question_text_short(self, obj):
        text = (obj.question_text or "").replace("\n", " ")
        return text[:60] + ("…" if len(text) > 60 else "")

    question_text_short.short_description = "Savol"

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener">'
                '<img src="{}" alt="Rasm" style="max-height:140px;max-width:100%;border-radius:8px;border:1px solid #ddd"></a>',
                obj.image.url,
                obj.image.url,
            )
        return "—"

    image_preview.short_description = "Rasm ko'rinishi"

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj and obj.image:
            ro.append("image_preview")
        return ro

    @admin.action(description="Savolni nusxalash (oxirgi order + 1)")
    def duplicate_questions(self, request, queryset):
        n = 0
        by_test = {}
        for q in queryset.select_related("test").order_by("test_id", "order", "pk"):
            test = q.test
            if test.pk not in by_test:
                last = test.questions.order_by("-order").values_list("order", flat=True).first()
                by_test[test.pk] = last or 0
            by_test[test.pk] += 1
            new_order = by_test[test.pk]
            image_data = None
            if q.image:
                image_data = (q.image.name, q.image.read())
            q.pk = None
            q._state.adding = True
            q.order = new_order
            if test.test_type == "reading":
                q.part_number = 1 if new_order <= 13 else (2 if new_order <= 26 else 3)
            elif test.test_type == "listening":
                if new_order <= 10:
                    q.part_number = 1
                elif new_order <= 20:
                    q.part_number = 2
                elif new_order <= 30:
                    q.part_number = 3
                else:
                    q.part_number = 4
            q.image = None
            q.save()
            if image_data:
                from django.core.files.base import ContentFile
                q.image.save(image_data[0], ContentFile(image_data[1]), save=True)
            n += 1
        self.message_user(request, f"{n} ta savol nusxalandi.", messages.SUCCESS)


@admin.register(MockAttempt)
class MockAttemptAdmin(admin.ModelAdmin):
    change_list_template = "admin/mock_tests/mockattempt_change_list.html"
    list_display = [
        "test",
        "short_session_key",
        "ielts_band",
        "score_percent",
        "correct_count",
        "total_questions",
        "is_finished",
        "started_at",
    ]
    list_filter = ["is_finished", "test__test_type", "started_at", "finished_at"]
    search_fields = ["session_key", "test__title"]
    ordering = ["-started_at"]
    list_select_related = ["test"]
    date_hierarchy = "started_at"
    readonly_fields = [
        "test",
        "session_key",
        "answers_json",
        "score_percent",
        "correct_count",
        "total_questions",
        "ielts_band",
        "is_finished",
        "started_at",
        "finished_at",
    ]
    fields = (
        "test",
        "session_key",
        ("score_percent", "ielts_band"),
        ("correct_count", "total_questions"),
        "is_finished",
        ("started_at", "finished_at"),
        "answers_json",
    )

    def short_session_key(self, obj):
        if not obj.session_key:
            return "-"
        return f"{obj.session_key[:8]}..."

    short_session_key.short_description = "Session"
