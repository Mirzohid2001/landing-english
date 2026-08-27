from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils import timezone
import re

from blog.models import (
    FAQ,
    LandingAICard,
    LandingBenefitCard,
    LandingHeroProof,
    LandingSectionCopy,
    LandingSettings,
    PlatformPreview,
    ProcessStep,
    PromoCampaign,
)


PURCHASE_STEPS = [
    {
        'step_number': 1,
        'title': 'Telegram tugmasini bosing',
        'description': 'Asosiy CTA orqali Telegram chatga o‘ting.',
        'icon': 'fab fa-telegram-plane',
    },
    {
        'step_number': 2,
        'title': 'Admin bilan bog‘laning',
        'description': 'Qaysi paket kerakligini yozing — 599k yoki LIVE bundle.',
        'icon': 'fas fa-comments',
    },
    {
        'step_number': 3,
        'title': 'To‘lovni amalga oshiring',
        'description': 'Admin sizga to‘lov usulini yuboradi.',
        'icon': 'fas fa-credit-card',
    },
    {
        'step_number': 4,
        'title': 'Login va parolni oling',
        'description': 'To‘lovdan keyin platformaga kirish ma’lumotlari — darhol o‘qishni boshlang.',
        'icon': 'fas fa-key',
    },
]

BENEFIT_CARDS = [
    {
        'icon': 'fas fa-chalkboard-teacher',
        'title': 'Jonli darslar',
        'text': 'Jonli darslar.',
        'badge': 'LIVE',
    },
    {
        'icon': 'fas fa-infinity',
        'title': 'Umrbod foydalanish',
        'text': 'Bir marta to‘lov — umrbod foydalanish. Yashirin to‘lovlar yo‘q.',
        'badge': 'Lifetime',
    },
    {
        'icon': 'fas fa-video',
        'title': '100+ video darslar',
        'text': 'IELTS bo‘yicha professional video darslar.',
        'badge': '100+',
    },
    {
        'icon': 'fas fa-robot',
        'title': 'Writing AI Checker',
        'text': 'Band score, xatolar va tavsiyalar — bir joyda.',
        'badge': 'AI',
    },
    {
        'icon': 'fas fa-headphones',
        'title': 'Reading & Listening amaliyoti',
        'text': 'Interaktiv mashqlar va testlar.',
        'badge': 'Practice',
    },
    {
        'icon': 'fas fa-chart-line',
        'title': 'Shaxsiy progress kabinetingiz',
        'text': 'Natija va progress tracking.',
        'badge': 'Progress',
    },
]

AI_CHECKER_CARDS = [
    {
        'key': 'writing',
        'icon': 'fas fa-pen-fancy',
        'title': 'Writing AI',
        'text': 'Band score, Task Achievement, Grammar va tavsiyalar.',
    },
    {
        'key': 'reading',
        'icon': 'fas fa-book-open',
        'title': 'Reading tahlili',
        'text': 'Correct/wrong, foiz va har bir savol tahlili.',
    },
    {
        'key': 'listening',
        'icon': 'fas fa-headphones',
        'title': 'Listening tahlili',
        'text': 'Audio, javoblar va statistika bir joyda.',
    },
]

HERO_PROOFS = [
    {
        'icon': 'fas fa-users',
        'title': '1000+',
        'subtitle': 'o‘quvchi',
    },
    {
        'icon': 'fas fa-trophy',
        'title': '7.0 / 7.5 / 8.0',
        'subtitle': 'haqiqiy natijalar',
    },
    {
        'icon': 'fas fa-chalkboard-teacher',
        'title': 'Jonli darslar',
        'subtitle': 'UK + 2 ustoz',
    },
    {
        'icon': 'fas fa-mobile-alt',
        'title': 'Mobil + Desktop',
        'subtitle': 'har joyda ishlaydi',
    },
]

SECTION_COPY_DEFAULTS = {
    'platform': {
        'kicker': 'Platforma',
        'title': 'Platforma ichida sizni nimalar kutadi?',
        'subtitle': 'Real dashboard, AI checker, jonli darslar va progress — barchasi bitta joyda.',
    },
    'benefits': {
        'kicker': '599 000 so‘m',
        'title': '599 000 so‘mga nimalar olasiz?',
        'subtitle': 'Jonli darslar, video kurslar, AI checker — bir martalik to‘lov bilan umrbod access.',
    },
    'ai': {
        'kicker': 'AI Checker',
        'title': 'AI checker qanday ishlaydi?',
        'subtitle': 'Writing, Reading va Listening — real product imkoniyatlari.',
    },
    'results': {
        'kicker': 'Natijalar',
        'title': 'Talabalarimizning natijalari',
        'subtitle': 'Haqiqiy score va sertifikatlar — faqat ruxsat bilan.',
    },
    'testimonials': {
        'kicker': 'Fikrlar',
        'title': 'Talabalar fikrlari',
        'subtitle': 'Video testimonial va haqiqiy tajribalar.',
    },
    'news': {
        'kicker': 'Yangiliklar',
        'title': 'Yangiliklar va takliflar',
        'subtitle': '',
    },
    'purchase': {
        'kicker': 'Xarid',
        'title': 'Qanday xarid qilinadi?',
        'subtitle': 'Telegram orqali 4 oddiy qadam.',
    },
    'faq': {
        'kicker': 'FAQ',
        'title': 'Ko‘p beriladigan savollar',
        'subtitle': 'To‘lov, access va product bo‘yicha eng muhim savollar.',
    },
}

DEFAULT_FAQS = [
    (
        'Bu oylik to‘lovmi?',
        'Yo‘q. 599 000 so‘m — bir martalik to‘lov. Umrbod platformaga kirish huquqi beriladi.',
    ),
    (
        'Umrbod access nimani anglatadi?',
        'Bir marta to‘lov qilasiz va platformaning barcha mavjud funksiyalaridan cheklovsiz foydalanasiz.',
    ),
    (
        'AI checker nimalarni tekshiradi?',
        'Writing, Reading va Listening bo‘limlarida natijalar, xatolar va tavsiyalar beriladi.',
    ),
    (
        'To‘lovdan keyin nima bo‘ladi?',
        'Admin Telegram orqali login va parol yuboradi. Shundan keyin darhol o‘qishni boshlaysiz.',
    ),
    (
        'Telefon orqali ishlaydimi?',
        'Ha, platforma mobil brauzerda ham ishlaydi.',
    ),
    (
        '599 000 so‘mga aynan nimalar kiradi?',
        'UK ustoz va yana 2 ta professional ustozdan jonli darslar, 100+ video darslar, AI checker, Reading/Listening/Writing materiallari, progress tracking va barcha yangilanishlar.',
    ),
    (
        'Jonli darslar bormi?',
        'Ha. UK ustoz va yana 2 ta professional ustozlardan jonli darslar mavjud. Qo‘shimcha LIVE bundle (899k) da Speaking + Reading LIVE darslar kengaytirilgan formatda beriladi.',
    ),
    (
        'Speaking bormi?',
        'Ha, jonli darslar orqali Speaking amaliyoti bor. LIVE bundle (899k) da Speaking + Reading LIVE darslar alohida kengaytirilgan paket sifatida taklif etiladi.',
    ),    (
        'Loginni qachon olaman?',
        'To‘lov tasdiqlangandan so‘ng, odatda bir necha soat ichida Telegram orqali.',
    ),
    (
        'To‘lovni qanday qilaman?',
        'Telegram orqali admin bilan bog‘lanib, qulay to‘lov usulini tanlaysiz.',
    ),
]


def get_active_promos(placement):
    now = timezone.now()
    qs = PromoCampaign.objects.filter(enabled=True, placement=placement)
    active = []
    for promo in qs:
        if promo.expires_at and now > promo.expires_at:
            continue
        active.append(promo)
    return active


PLATFORM_TABS = [
    ('all', 'Barchasi'),
    ('writing', 'Writing AI'),
    ('reading', 'Reading'),
    ('listening', 'Listening'),
    ('videos', 'Video darslar'),
    ('progress', 'Progress'),
]

PLATFORM_RESPONSIVE_WIDTHS = (640, 960, 1200)
PLANET_RESPONSIVE_WIDTHS = (180, 280, 360)


def _static_url(path):
    return staticfiles_storage.url(path)


def build_static_picture(
    stem,
    *,
    alt='',
    widths=PLATFORM_RESPONSIVE_WIDTHS,
    sizes='(max-width: 768px) 92vw, min(1100px, 90vw)',
    aspect_w=1200,
    aspect_h=720,
    class_name='',
):
    """Responsive <picture> data for static/images/landing assets (WebP + PNG)."""
    webp_parts = []
    png_parts = []
    for width in widths:
        webp_parts.append(f'{_static_url(f"{stem}-{width}.webp")} {width}w')
        png_parts.append(f'{_static_url(f"{stem}-{width}.png")} {width}w')
    fallback_w = widths[-1]
    return {
        'alt': alt,
        'sizes': sizes,
        'webp_srcset': ', '.join(webp_parts),
        'png_srcset': ', '.join(png_parts),
        'fallback': _static_url(f'{stem}-{fallback_w}.png'),
        'width': aspect_w,
        'height': aspect_h,
        'class_name': class_name,
        'is_responsive': True,
    }


def build_media_picture(url, *, alt='', class_name='', width=1200, height=720, sizes=''):
    """Single-src picture wrapper for admin-uploaded media (no generated variants yet)."""
    return {
        'alt': alt,
        'sizes': sizes or '(max-width: 768px) 92vw, min(1100px, 90vw)',
        'webp_srcset': '',
        'png_srcset': '',
        'fallback': url,
        'width': width,
        'height': height,
        'class_name': class_name,
        'is_responsive': False,
    }


def platform_fallback_picture(tab_key, alt=''):
    return build_static_picture(
        f'images/landing/platform-{tab_key}',
        alt=alt or f'Ton Academy — {tab_key}',
        class_name='lp-preview__img',
    )


def ai_fallback_picture(card_key, alt=''):
    mapping = {
        'writing': 'platform-writing',
        'reading': 'platform-reading',
        'listening': 'platform-listening',
    }
    asset = mapping.get(card_key, 'platform-all')
    return build_static_picture(
        f'images/landing/{asset}',
        alt=alt or card_key,
        sizes='(max-width: 768px) 92vw, 360px',
        class_name='lp-ai-card__shot',
    )


def get_planet_picture():
    return build_static_picture(
        'images/landing/planet',
        alt='',
        widths=PLANET_RESPONSIVE_WIDTHS,
        sizes='(max-width: 768px) 140px, 180px',
        aspect_w=360,
        aspect_h=360,
        class_name='lp-planet__img',
    )


# Backwards-compatible helpers used by older tests/templates
def platform_fallback_image(tab_key):
    return _static_url(f'images/landing/platform-{tab_key}-1200.webp')


def ai_fallback_image(card_key):
    mapping = {
        'writing': 'platform-writing',
        'reading': 'platform-reading',
        'listening': 'platform-listening',
    }
    asset = mapping.get(card_key, 'platform-all')
    return _static_url(f'images/landing/{asset}-960.webp')


def get_platform_tabs():
    previews = {
        preview.tab: preview
        for preview in PlatformPreview.objects.filter(is_active=True)
    }
    tabs = []
    for key, label in PLATFORM_TABS:
        preview = previews.get(key)
        alt_text = preview.alt_text if preview and preview.alt_text else f'Ton Academy — {label}'
        if preview and preview.image:
            picture = build_media_picture(
                preview.image.url,
                alt=alt_text,
                class_name='lp-preview__img',
            )
            image_url = preview.image.url
        else:
            picture = platform_fallback_picture(key, alt=alt_text)
            image_url = picture['fallback']
        tabs.append({
            'key': key,
            'label': label,
            'title': preview.title if preview else label,
            'image_url': image_url,
            'picture': picture,
            'alt_text': alt_text,
        })
    return tabs


def get_section_copy():
    data = {
        item.section: item
        for item in LandingSectionCopy.objects.filter(is_active=True)
    }
    resolved = {}
    for key, defaults in SECTION_COPY_DEFAULTS.items():
        item = data.get(key)
        resolved[key] = {
            'kicker': item.kicker if item else defaults['kicker'],
            'title': item.title if item else defaults['title'],
            'subtitle': item.subtitle if item else defaults['subtitle'],
        }
    return resolved


def get_benefit_cards():
    qs = LandingBenefitCard.objects.filter(is_active=True).order_by('order', 'id')
    if qs.exists():
        return [
            {
                'icon': card.icon,
                'title': card.title,
                'text': card.text,
                'badge': card.badge,
            }
            for card in qs
        ]
    return BENEFIT_CARDS


def _extract_youtube_id(url):
    if not url:
        return ''
    patterns = (
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?.*[&?]v=([a-zA-Z0-9_-]{11})',
    )
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ''


def get_ai_checker_cards():
    cards = {
        card.key: card
        for card in LandingAICard.objects.filter(is_active=True)
    }
    resolved = []
    for order, default in enumerate(AI_CHECKER_CARDS):
        card = cards.get(default['key'])
        title = card.title if card else default['title']
        video_file_url = ''
        video_url = ''
        poster_url = ''
        youtube_id = ''
        if card:
            if card.video_file:
                video_file_url = card.video_file.url
            video_url = (card.video_url or '').strip()
            youtube_id = _extract_youtube_id(video_url)
            if card.poster_image:
                poster_url = card.poster_image.url
        has_video = bool(video_file_url or video_url)
        video_mime = 'video/mp4'
        if video_file_url.lower().endswith('.webm'):
            video_mime = 'video/webm'
        elif video_file_url.lower().endswith('.ogg') or video_file_url.lower().endswith('.ogv'):
            video_mime = 'video/ogg'
        resolved.append({
            'key': default['key'],
            'icon': card.icon if card else default['icon'],
            'title': title,
            'text': card.text if card else default['text'],
            'picture': ai_fallback_picture(default['key'], alt=title),
            'image_url': ai_fallback_image(default['key']),
            'has_video': has_video,
            'video_file_url': video_file_url,
            'video_mime': video_mime,
            'video_url': video_url,
            'youtube_id': youtube_id,
            'poster_url': poster_url,
            'order': card.order if card else order,
        })
    return sorted(resolved, key=lambda item: item['order'])


def get_hero_proofs():
    qs = LandingHeroProof.objects.filter(is_active=True).order_by('order', 'id')
    if qs.exists():
        return [
            {
                'icon': item.icon,
                'title': item.title,
                'subtitle': item.subtitle,
            }
            for item in qs
        ]
    return HERO_PROOFS


def normalize_purchase_steps():
    qs = ProcessStep.objects.filter(is_active=True, flow='purchase').order_by('order', 'step_number')
    if qs.exists():
        return [
            {
                'step_number': step.step_number,
                'title': step.title,
                'description': step.description,
                'icon': step.icon,
            }
            for step in qs
        ]
    return PURCHASE_STEPS


def get_site_chrome_context():
    """Nav, announcement va footer uchun yengil landing kontekst."""
    settings = LandingSettings.get_solo()
    announcement = get_active_promos('announcement')[:1]
    return {
        'landing': settings,
        'announcement_promo': announcement[0] if announcement else None,
    }


def get_landing_context():
    settings = LandingSettings.get_solo()
    announcement = get_active_promos('announcement')[:1]
    current_offer = get_active_promos('current_offer')[:1]
    news_promos = get_active_promos('news')[:4]
    platform_previews = PlatformPreview.objects.filter(is_active=True)
    faqs = FAQ.objects.filter(is_active=True)
    return {
        **get_site_chrome_context(),
        'current_offer_promo': current_offer[0] if current_offer else None,
        'news_promos': news_promos,
        'section_copy': get_section_copy(),
        'platform_previews': platform_previews,
        'platform_tabs': get_platform_tabs(),
        'benefit_cards': get_benefit_cards(),
        'ai_checker_cards': get_ai_checker_cards(),
        'hero_proofs': get_hero_proofs(),
        'planet_picture': get_planet_picture(),
        'purchase_steps': normalize_purchase_steps(),
        'faqs': faqs,
    }
