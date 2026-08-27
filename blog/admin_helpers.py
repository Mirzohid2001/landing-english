"""Shared helpers for Ton Academy Django admin."""

from django.contrib import admin, messages
from django.utils.html import format_html


def admin_thumb(image_field, size=52):
    """Return an HTML thumbnail or an em dash."""
    if not image_field:
        return '—'
    try:
        url = image_field.url
    except ValueError:
        return '—'
    return format_html(
        '<img src="{}" alt="" width="{}" height="{}" '
        'style="object-fit:cover;border-radius:8px;border:1px solid #d0d7de;'
        'background:#0b1224;vertical-align:middle;" />',
        url,
        size,
        size,
    )


def bool_badge(value, yes='Yoqilgan', no='O‘chiq'):
    if value:
        return format_html(
            '<span style="display:inline-block;padding:2px 8px;border-radius:999px;'
            'background:#dafbe1;color:#116329;font-weight:700;font-size:12px;">{}</span>',
            yes,
        )
    return format_html(
        '<span style="display:inline-block;padding:2px 8px;border-radius:999px;'
        'background:#ffebe9;color:#a40e26;font-weight:700;font-size:12px;">{}</span>',
        no,
    )


def _toggle_field(model):
    for name in ('is_active', 'enabled', 'show_on_homepage', 'is_featured'):
        if hasattr(model, name):
            return name
    return None


@admin.action(description='Tanlanganlarni yoqish')
def make_active(modeladmin, request, queryset):
    field = _toggle_field(queryset.model)
    if not field:
        modeladmin.message_user(request, 'Bu modelda yoqish/o‘chirish maydoni yo‘q.', messages.ERROR)
        return
    updated = queryset.update(**{field: True})
    modeladmin.message_user(request, f'{updated} ta yozuv yoqildi.', messages.SUCCESS)


@admin.action(description='Tanlanganlarni o‘chirish')
def make_inactive(modeladmin, request, queryset):
    field = _toggle_field(queryset.model)
    if not field:
        modeladmin.message_user(request, 'Bu modelda yoqish/o‘chirish maydoni yo‘q.', messages.ERROR)
        return
    updated = queryset.update(**{field: False})
    modeladmin.message_user(request, f'{updated} ta yozuv o‘chirildi.', messages.WARNING)


class LandingCMSMixin:
    """Common UX for landing content models."""

    save_on_top = True
    list_per_page = 25
    actions = (make_active, make_inactive)

    class Media:
        css = {'all': ('css/admin_landing.css',)}
