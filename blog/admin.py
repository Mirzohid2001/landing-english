from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .admin_helpers import (
    LandingCMSMixin,
    admin_thumb,
    bool_badge,
    make_active,
    make_inactive,
)
from .models import (
    About,
    ContactRequest,
    Course,
    CourseApplication,
    FAQ,
    Feature,
    IELTSCertificate,
    LandingAICard,
    LandingBenefitCard,
    LandingHeroProof,
    LandingSectionCopy,
    LandingSettings,
    PlatformPreview,
    ProcessStep,
    PromoCampaign,
    SATCourse,
    StudentResult,
    Teacher,
    TelegramConfig,
    Testimonial,
    Video,
)


# ——— Legacy / general content ———


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'level', 'price', 'duration', 'is_featured', 'created_at']
    list_filter = ['level', 'is_featured', 'created_at']
    search_fields = ['title', 'description']
    save_on_top = True
    fieldsets = (
        ('Asosiy', {
            'fields': ('title', 'description', 'level', 'price', 'image', 'is_featured'),
        }),
        ('Video', {
            'fields': ('promo_video_file',),
            'description': 'MP4 / WebM yuklang.',
        }),
    )

    def save_model(self, request, obj, form, change):
        obj.duration = 'Umrbod'
        super().save_model(request, obj, form, change)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['name', 'specialization', 'experience', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'specialization', 'bio']
    list_editable = ['is_active']
    save_on_top = True
    actions = (make_active, make_inactive)
    fieldsets = (
        ('Ustoz', {
            'fields': ('name', 'photo', 'bio', 'specialization', 'experience', 'is_active'),
        }),
        ('Video', {
            'fields': ('video_file',),
        }),
    )


@admin.register(Testimonial)
class TestimonialAdmin(LandingCMSMixin, admin.ModelAdmin):
    list_display = ['thumb', 'student_name', 'rating', 'course', 'is_featured', 'created_at']
    list_filter = ['rating', 'is_featured', 'course', 'created_at']
    search_fields = ['student_name', 'text']
    list_editable = ['is_featured']
    readonly_fields = ['photo_preview']
    fieldsets = (
        ('O‘quvchi fikri', {
            'fields': (
                'student_name', 'student_photo', 'photo_preview',
                'text', 'rating', 'course', 'is_featured',
            ),
            'description': 'Landing “Fikrlar” bo‘limida chiqadi (is_featured = True).',
        }),
        ('Video testimonial', {
            'fields': ('video_file',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Foto')
    def thumb(self, obj):
        return admin_thumb(obj.student_photo)

    @admin.display(description='Preview')
    def photo_preview(self, obj):
        return admin_thumb(obj.student_photo, size=120)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'video_type', 'course', 'order', 'is_active', 'created_at']
    list_filter = ['video_type', 'is_active', 'course', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['order', 'is_active']
    save_on_top = True
    actions = (make_active, make_inactive)
    fieldsets = (
        ('Video', {
            'fields': ('title', 'description', 'video_type', 'course', 'order', 'is_active'),
        }),
        ('Fayl / URL', {
            'fields': ('video_url', 'video_file', 'preview_image'),
        }),
    )


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'is_processed', 'created_at']
    list_filter = ['is_processed', 'created_at']
    search_fields = ['name', 'email', 'phone', 'message']
    readonly_fields = ['created_at']
    list_editable = ['is_processed']
    date_hierarchy = 'created_at'


@admin.register(CourseApplication)
class CourseApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'course', 'status', 'created_at']
    list_filter = ['status', 'course', 'created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['created_at']
    list_editable = ['status']
    date_hierarchy = 'created_at'


@admin.register(About)
class AboutAdmin(admin.ModelAdmin):
    list_display = ['title', 'updated_at']
    save_on_top = True
    fieldsets = (
        ('Kontent', {
            'fields': ('title', 'text', 'mission', 'achievements', 'image'),
        }),
        ('Video', {
            'fields': ('video_file',),
            'classes': ('collapse',),
        }),
    )


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['title', 'icon', 'order', 'is_active']
    list_filter = ['is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'description']
    actions = (make_active, make_inactive)


@admin.register(IELTSCertificate)
class IELTSCertificateAdmin(LandingCMSMixin, admin.ModelAdmin):
    list_display = [
        'thumb', 'student_name', 'ielts_score', 'course',
        'date_obtained', 'show_on_homepage', 'created_at',
    ]
    list_filter = ['show_on_homepage', 'course', 'date_obtained']
    search_fields = ['student_name']
    list_editable = ['show_on_homepage', 'ielts_score']
    readonly_fields = ['certificate_preview', 'photo_preview']
    date_hierarchy = 'date_obtained'
    fieldsets = (
        ('O‘quvchi', {
            'fields': (
                'student_name', 'student_photo', 'photo_preview',
                'ielts_score', 'date_obtained', 'course', 'show_on_homepage',
            ),
            'description': 'Landing “Natijalar / sertifikatlar” swipe qatorida chiqadi.',
        }),
        ('Sertifikat rasmi', {
            'fields': ('certificate_image', 'certificate_preview'),
        }),
    )
    actions = (
        'show_on_home',
        'hide_from_home',
    )

    @admin.display(description='Foto')
    def thumb(self, obj):
        return admin_thumb(obj.student_photo or obj.certificate_image)

    @admin.display(description='Sertifikat preview')
    def certificate_preview(self, obj):
        return admin_thumb(obj.certificate_image, size=180)

    @admin.display(description='Foto preview')
    def photo_preview(self, obj):
        return admin_thumb(obj.student_photo, size=120)

    @admin.action(description='Homepageda ko‘rsatish')
    def show_on_home(self, request, queryset):
        updated = queryset.update(show_on_homepage=True)
        self.message_user(request, f'{updated} ta sertifikat homepage ga qo‘yildi.')

    @admin.action(description='Homepagedan yashirish')
    def hide_from_home(self, request, queryset):
        updated = queryset.update(show_on_homepage=False)
        self.message_user(request, f'{updated} ta sertifikat yashirildi.')


@admin.register(FAQ)
class FAQAdmin(LandingCMSMixin, admin.ModelAdmin):
    list_display = ['question_short', 'order', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['question', 'answer']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'id']
    fieldsets = (
        ('FAQ', {
            'fields': ('question', 'answer', 'order', 'is_active'),
            'description': 'Landing pastidagi accordion. Qisqa savol + aniq javob yozing.',
        }),
    )

    @admin.display(description='Savol', ordering='question')
    def question_short(self, obj):
        text = obj.question or ''
        return text if len(text) <= 80 else f'{text[:77]}…'


@admin.register(ProcessStep)
class ProcessStepAdmin(LandingCMSMixin, admin.ModelAdmin):
    list_display = ['step_number', 'title', 'flow', 'icon', 'order', 'is_active']
    list_filter = ['flow', 'is_active']
    search_fields = ['title', 'description']
    list_editable = ['order', 'is_active']
    ordering = ['flow', 'order', 'step_number']
    fieldsets = (
        ('Qadam', {
            'fields': ('flow', 'step_number', 'title', 'description', 'icon', 'order', 'is_active'),
            'description': (
                'Xarid oqimi uchun flow = purchase. Icon: Font Awesome class, '
                'masalan fas fa-telegram.'
            ),
        }),
    )


@admin.register(StudentResult)
class StudentResultAdmin(LandingCMSMixin, admin.ModelAdmin):
    list_display = [
        'thumb', 'full_name', 'course', 'achievement',
        'is_featured', 'order', 'is_active',
    ]
    list_filter = ['is_active', 'is_featured', 'course']
    search_fields = ['first_name', 'last_name', 'bio', 'achievement']
    list_editable = ['is_featured', 'order', 'is_active']
    readonly_fields = ['photo_preview']
    fieldsets = (
        ('O‘quvchi', {
            'fields': (
                'first_name', 'last_name', 'photo', 'photo_preview',
                'bio', 'course', 'achievement',
            ),
        }),
        ('Video', {
            'fields': ('video_file', 'video_url'),
            'classes': ('collapse',),
        }),
        ('Ko‘rsatish', {
            'fields': ('is_featured', 'order', 'is_active'),
            'description': 'is_featured = True bo‘lsa landing natijalarida chiqadi.',
        }),
    )

    @admin.display(description='To‘liq ism', ordering='first_name')
    def full_name(self, obj):
        return obj.full_name

    @admin.display(description='Foto')
    def thumb(self, obj):
        return admin_thumb(obj.photo)

    @admin.display(description='Preview')
    def photo_preview(self, obj):
        return admin_thumb(obj.photo, size=120)


@admin.register(SATCourse)
class SATCourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'level', 'price', 'duration', 'order', 'is_active', 'created_at']
    list_filter = ['level', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['order', 'is_active']
    save_on_top = True
    actions = (make_active, make_inactive)


@admin.register(TelegramConfig)
class TelegramConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'masked_bot_token', 'chat_ids_count', 'is_active', 'updated_at']
    list_filter = ['is_active', 'updated_at']
    search_fields = ['name', 'chat_ids']
    list_editable = ['is_active']
    save_on_top = True
    fieldsets = (
        ('Telegram bot', {
            'fields': ('name', 'bot_token', 'chat_ids', 'is_active'),
            'description': 'Chat ID larni har bir qatorda bitta yozing. Token maxfiy saqlanadi.',
        }),
    )

    @admin.display(description='Chat ID soni')
    def chat_ids_count(self, obj):
        return len(obj.get_chat_ids_list())

    @admin.display(description='Bot token')
    def masked_bot_token(self, obj):
        if len(obj.bot_token) <= 10:
            return '********'
        return f'{obj.bot_token[:6]}…{obj.bot_token[-4:]}'


# ——— Landing CMS (asosiy) ———


@admin.register(LandingSettings)
class LandingSettingsAdmin(LandingCMSMixin, admin.ModelAdmin):
    list_display = ['label', 'formatted_price', 'ga4_status', 'posthog_status', 'updated_at', 'open_site']
    readonly_fields = ['updated_at', 'open_site', 'quick_guide']
    actions = None
    fieldsets = (
        (None, {
            'fields': ('quick_guide', 'open_site'),
        }),
        ('1. Hero matnlari', {
            'fields': (
                'hero_badge_text', 'hero_headline', 'hero_subtitle',
                'primary_cta_text', 'secondary_cta_text', 'reassurance_text',
            ),
            'description': 'Birinchi ekran. Headline da yangi qator uchun Enter ishlating.',
        }),
        ('2. Narx kartasi (599k)', {
            'fields': (
                'base_price', 'base_price_label', 'pricing_card_title', 'pricing_card_badge',
            ),
        }),
        ('3. CTA havolalari', {
            'fields': ('telegram_purchase_url', 'free_trial_url'),
        }),
        ('4. Statistika (sahifa matnlari)', {
            'fields': (
                'stat_students', 'stat_students_label',
                'stat_improvement', 'stat_improvement_label',
            ),
            'classes': ('collapse',),
        }),
        ('5. Aloqa / ijtimoiy', {
            'fields': ('instagram_url', 'youtube_url', 'support_hours'),
        }),
        ('6. Analytics (GA4 + PostHog)', {
            'fields': (
                'ga4_measurement_id',
                'posthog_project_api_key',
                'posthog_api_host',
                'updated_at',
            ),
            'description': (
                'GA4: Google Analytics. PostHog: sahifa view, session, click eventlar '
                '(us.posthog.com). Token klientdan olingan phc_… kalit.'
            ),
        }),
    )

    def has_add_permission(self, request):
        return not LandingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='Sozlama')
    def label(self, obj):
        return 'Landing sozlamalari'

    @admin.display(description='Narx')
    def formatted_price(self, obj):
        return f'{obj.formatted_base_price()} so‘m'

    @admin.display(description='GA4')
    def ga4_status(self, obj):
        return bool_badge(bool(obj.ga4_measurement_id), yes=obj.ga4_measurement_id or 'Yoqilgan', no='Yo‘q')

    @admin.display(description='PostHog')
    def posthog_status(self, obj):
        return bool_badge(bool(obj.posthog_project_api_key), yes='Yoqilgan', no='Yo‘q')

    @admin.display(description='Sayt')
    def open_site(self, obj=None):
        try:
            url = reverse('blog:home')
        except Exception:
            url = '/'
        return format_html(
            '<a class="button" href="{}" target="_blank" rel="noopener">Landingni ochish ↗</a>',
            url,
        )

    @admin.display(description='Qisqa yo‘riqnoma')
    def quick_guide(self, obj=None):
        return format_html(
            '<div class="admin-hint">'
            '<strong>Qayerni qayerdan o‘zgartirasiz?</strong><br>'
            '• Tepa LIVE banner / dolzarb taklif → <em>Promo kampaniyalar</em><br>'
            '• Bo‘lim sarlavhalari → <em>Bo‘lim matnlari</em><br>'
            '• Hero isbotlar / benefit / AI kartalar → tegishli menyular<br>'
            '• Platforma skrinshotlari → <em>Platforma previewlar</em><br>'
            '• Sertifikat, o‘quvchi, fikr → Natijalar / Testimonials'
            '</div>'
        )


@admin.register(PromoCampaign)
class PromoCampaignAdmin(LandingCMSMixin, admin.ModelAdmin):
    list_display = [
        'title_short', 'placement', 'badge', 'price_display',
        'live_now', 'enabled', 'expires_at', 'order',
    ]
    list_filter = ['placement', 'enabled', 'badge']
    list_editable = ['enabled', 'order']
    search_fields = ['title', 'campaign_id', 'description', 'offer_label']
    ordering = ['placement', 'order', '-created_at']
    readonly_fields = ['created_at', 'updated_at', 'image_preview', 'live_now']
    date_hierarchy = 'expires_at'
    fieldsets = (
        ('Holat', {
            'fields': ('enabled', 'live_now', 'placement', 'order'),
        }),
        ('Matn', {
            'fields': ('badge', 'badge_custom', 'title', 'description', 'offer_label', 'urgency_text'),
            'description': (
                'Announcement (tepa banner) uchun title qisqa bo‘lsin — narx avtomatik '
                'qo‘shiladi. badge_custom to‘ldirilsa, odatiy badge o‘rniga shu chiqadi.'
            ),
        }),
        ('Narx va CTA', {
            'fields': ('price', 'cta_text', 'cta_link', 'campaign_id'),
        }),
        ('Muddat', {
            'fields': ('start_date', 'expires_at'),
            'classes': ('collapse',),
        }),
        ('Rasm', {
            'fields': ('image', 'image_preview'),
            'classes': ('collapse',),
        }),
        ('Meta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Sarlavha', ordering='title')
    def title_short(self, obj):
        text = obj.title or ''
        return text if len(text) <= 56 else f'{text[:53]}…'

    @admin.display(description='Narx', ordering='price')
    def price_display(self, obj):
        if not obj.price:
            return '—'
        return f'{obj.formatted_price()} so‘m'

    @admin.display(description='Hozir aktiv?', boolean=True)
    def live_now(self, obj):
        return obj.is_active_now

    @admin.display(description='Rasm preview')
    def image_preview(self, obj):
        return admin_thumb(obj.image, size=160)


@admin.register(PlatformPreview)
class PlatformPreviewAdmin(LandingCMSMixin, admin.ModelAdmin):
    list_display = ['thumb', 'tab', 'title', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active', 'tab']
    search_fields = ['title', 'alt_text']
    ordering = ['order', 'tab']
    readonly_fields = ['image_preview']
    fieldsets = (
        ('Tab', {
            'fields': ('tab', 'title', 'alt_text', 'order', 'is_active'),
        }),
        ('Screenshot', {
            'fields': ('image', 'image_preview'),
            'description': (
                'Real platforma skrinshotini yuklang (WebP/PNG, ~1200px kenglik tavsiya). '
                'Bo‘sh qolsa default placeholder ishlatiladi.'
            ),
        }),
    )

    @admin.display(description='Rasm')
    def thumb(self, obj):
        return admin_thumb(obj.image)

    @admin.display(description='Preview')
    def image_preview(self, obj):
        return admin_thumb(obj.image, size=280)


@admin.register(LandingSectionCopy)
class LandingSectionCopyAdmin(LandingCMSMixin, admin.ModelAdmin):
    list_display = ['section', 'kicker', 'title_short', 'is_active']
    list_filter = ['section', 'is_active']
    search_fields = ['kicker', 'title', 'subtitle']
    list_editable = ['is_active']
    ordering = ['section']
    fieldsets = (
        ('Bo‘lim matni', {
            'fields': ('section', 'kicker', 'title', 'subtitle', 'is_active'),
            'description': 'Har bir landing bo‘limining kicker / title / subtitle matni.',
        }),
    )

    @admin.display(description='Sarlavha', ordering='title')
    def title_short(self, obj):
        text = obj.title or ''
        return text if len(text) <= 60 else f'{text[:57]}…'


@admin.register(LandingHeroProof)
class LandingHeroProofAdmin(LandingCMSMixin, admin.ModelAdmin):
    list_display = ['order', 'icon', 'title', 'subtitle', 'is_active']
    list_display_links = ['title']
    list_filter = ['is_active']
    search_fields = ['title', 'subtitle', 'icon']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'id']
    fieldsets = (
        ('Hero proof', {
            'fields': ('icon', 'title', 'subtitle', 'order', 'is_active'),
            'description': 'Icon: Font Awesome, masalan fas fa-chalkboard-teacher.',
        }),
    )


@admin.register(LandingBenefitCard)
class LandingBenefitCardAdmin(LandingCMSMixin, admin.ModelAdmin):
    list_display = ['order', 'icon', 'title', 'badge', 'is_active']
    list_display_links = ['title']
    list_filter = ['is_active']
    search_fields = ['title', 'text', 'badge']
    list_editable = ['order', 'is_active', 'badge']
    ordering = ['order', 'id']
    fieldsets = (
        ('Benefit kartasi', {
            'fields': ('icon', 'title', 'text', 'badge', 'order', 'is_active'),
            'description': '“599 000 so‘mga nimalar olasiz?” grid kartalari.',
        }),
    )


@admin.register(LandingAICard)
class LandingAICardAdmin(LandingCMSMixin, admin.ModelAdmin):
    list_display = ['order', 'key', 'title', 'has_media', 'icon', 'is_active']
    list_display_links = ['title']
    list_filter = ['key', 'is_active']
    search_fields = ['title', 'text', 'icon', 'video_url']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'id']
    readonly_fields = ['poster_preview']
    fieldsets = (
        ('Matn', {
            'fields': ('key', 'icon', 'title', 'text', 'order', 'is_active'),
            'description': 'key ni o‘zgartirmang (writing / reading / listening) — analytics bog‘liq.',
        }),
        ('Video (rasm o‘rniga)', {
            'fields': ('video_file', 'video_url', 'poster_image', 'poster_preview'),
            'description': (
                'Asosan MP4 yuklang. Yoki YouTube havola qo‘ying. '
                'Video bo‘lmasa eski placeholder rasm chiqadi.'
            ),
        }),
    )

    @admin.display(description='Media', boolean=True)
    def has_media(self, obj):
        return obj.has_video

    @admin.display(description='Poster preview')
    def poster_preview(self, obj):
        return admin_thumb(obj.poster_image, size=160)


# Admin index: Landing CMS modellari tepaga
_LANDING_ORDER = [
    'LandingSettings',
    'PromoCampaign',
    'LandingSectionCopy',
    'LandingHeroProof',
    'LandingBenefitCard',
    'LandingAICard',
    'PlatformPreview',
    'ProcessStep',
    'FAQ',
    'IELTSCertificate',
    'StudentResult',
    'Testimonial',
    'ContactRequest',
    'CourseApplication',
    'TelegramConfig',
]


def _patch_admin_ordering():
    original = admin.AdminSite.get_app_list

    def get_app_list(self, request, app_label=None):
        app_list = original(self, request, app_label=app_label)
        for app in app_list:
            if app.get('app_label') != 'blog':
                continue
            models = app.get('models', [])
            rank = {name: idx for idx, name in enumerate(_LANDING_ORDER)}

            def sort_key(model):
                object_name = model.get('object_name') or ''
                return (rank.get(object_name, 500), model.get('name', ''))

            app['models'] = sorted(models, key=sort_key)
        return app_list

    admin.AdminSite.get_app_list = get_app_list


_patch_admin_ordering()
