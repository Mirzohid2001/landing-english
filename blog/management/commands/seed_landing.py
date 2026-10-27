from datetime import date, timedelta

from django.core.management.base import BaseCommand

from blog.models import (
    FAQ,
    IELTSCertificate,
    LandingAICard,
    LandingBenefitCard,
    LandingHeroProof,
    LandingSectionCopy,
    LandingSettings,
    PlatformPreview,
    ProcessStep,
    PromoCampaign,
    StudentResult,
    Testimonial,
)
from blog.services.landing import (
    AI_CHECKER_CARDS,
    BENEFIT_CARDS,
    DEFAULT_FAQS,
    HERO_PROOFS,
    PLATFORM_TABS,
    PURCHASE_STEPS,
    SECTION_COPY_DEFAULTS,
)

GA4_ID = 'G-6NKQ1LZYD0'
POSTHOG_KEY = 'phc_CBNfRo5dzYZE7zJK8VT5VwkvwyGdB8NJBEtjSP9YYYFT'
POSTHOG_HOST = 'https://us.i.posthog.com'

HERO_DEFAULTS = {
    'hero_headline': 'Kafolatlangan /\nIELTS - 7.0 + Online program',
    'hero_subtitle': (
        'IELTS balingizni Britaniyalik ustozlar va kafolatlangan tizim orqali o‘rganing'
    ),
    # Eski default seed da yo‘q edi → production da “joylar cheklangan” qotib qolgan.
    'hero_badge_text': 'UK ustoz + jonli darslar — joylar cheklangan',
    'primary_cta_text': 'Bepul daraja testini boshlash',
    'secondary_cta_text': 'Telegram orqali xarid qilish',
    'base_price_label': 'Platforma + jonli darslar — study plan',
    'pricing_card_title': 'Study plan',
    'reassurance_text': 'Bir martalik to‘lov • Jonli darslar • Study plan',
    'instagram_url': 'https://www.instagram.com/tonacademyuz/',
    'youtube_url': 'https://www.youtube.com/@TonAcademyuz',
    'telegram_purchase_url': 'https://t.me/tonacademyuz',
    'platform_url': 'https://tonielts.uz/',
    'support_hours': 'Dush–Shan: 09:00–20:00',
    'ga4_measurement_id': GA4_ID,
    'posthog_project_api_key': POSTHOG_KEY,
    'posthog_api_host': POSTHOG_HOST,
}

LIVE_BUNDLE = {
    'badge': 'live',
    'title': 'Jonli darslar',
    'description': 'Jonli darslar + to‘liq website access',
    'offer_label': 'LIVE bundle — 899 000 so‘m',
    'price': 899_000,
    'urgency_text': 'Joylar cheklangan',
    'cta_text': 'Telegram orqali qo‘shilish',
    'cta_link': 'https://t.me/tonacademyuz',
}

DEMO_CERTIFICATES = [
    ('Aziza Karimova', 7.5),
    ('Jasur Toshmatov', 7.0),
    ('Madina Rahimova', 8.0),
    ('Bobur Aliyev', 7.5),
]

DEMO_STUDENTS = [
    ('Dilnoza', 'Yusupova', 'IELTS 7.5', 'Platformadagi AI checker va video darslar yordamida 6.5 dan 7.5 ga chiqdim.'),
    ('Sardor', 'Mirzayev', 'IELTS 7.0', 'Reading va Listening mashqlari haqiqiy imtihonga juda o‘xshash edi.'),
    ('Nilufar', 'Qodirova', 'IELTS 8.0', 'Writing AI tavsiyalari band score ni tez oshirishga yordam berdi.'),
    ('Otabek', 'Normatov', 'IELTS 7.5', 'Platforma va study plan yordamida bir martalik to‘lov bilan natijaga chiqdim.'),
]

DEMO_TESTIMONIALS = [
    ('Zuhra', 'Toshpo‘lova', 5, 'AI Writing checker band score va grammar xatolarini aniq ko‘rsatadi. 6.0 dan 7.0 ga chiqdim.'),
    ('Farhod', 'Ergashev', 5, 'Video darslar tushunarli, platforma qulay. Telegram orqali tez login oldim.'),
    ('Sevara', 'Ismoilova', 5, 'Reading tahlili har bir savolni tushunishga yordam beradi. Natija 7.5.'),
    ('Jamshid', 'Abdurahmonov', 5, 'Mock testlar va platforma bir joyda — bepul sinab ko‘rib, keyin sotib oldim.'),
]


def seed_demo_social_proof():
    created = {'certificates': 0, 'students': 0, 'testimonials': 0}
    today = date.today()

    for order, (name, score) in enumerate(DEMO_CERTIFICATES):
        _, was_created = IELTSCertificate.objects.get_or_create(
            student_name=name,
            defaults={
                'ielts_score': score,
                'date_obtained': today - timedelta(days=30 + order * 10),
                'show_on_homepage': True,
            },
        )
        if was_created:
            created['certificates'] += 1

    for order, (first, last, achievement, bio) in enumerate(DEMO_STUDENTS):
        _, was_created = StudentResult.objects.get_or_create(
            first_name=first,
            last_name=last,
            defaults={
                'achievement': achievement,
                'bio': bio,
                'is_featured': True,
                'is_active': True,
                'order': order,
            },
        )
        if was_created:
            created['students'] += 1

    for order, (first, last, rating, text) in enumerate(DEMO_TESTIMONIALS):
        name = f'{first} {last}'
        _, was_created = Testimonial.objects.get_or_create(
            student_name=name,
            defaults={
                'text': text,
                'rating': rating,
                'is_featured': True,
            },
        )
        if was_created:
            created['testimonials'] += 1

    return created


class Command(BaseCommand):
    help = 'Landing sahifa uchun default sozlamalar, FAQ, platform preview va promo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--enable-promo',
            action='store_true',
            help='899k LIVE announcement + dolzarb taklifni yoqish',
        )
        parser.add_argument(
            '--disable-promo',
            action='store_true',
            help='LIVE announcement + dolzarb taklifni o‘chirish',
        )
        parser.add_argument(
            '--deploy',
            action='store_true',
            help='Production: promo + GA4 + demo natijalar/testimonials',
        )

    def handle(self, *args, **options):
        deploy = options['deploy']
        enable_promo = options['enable_promo'] or deploy
        disable_promo = options['disable_promo']
        if enable_promo and disable_promo:
            self.stderr.write(self.style.ERROR('--enable-promo va --disable-promo birga ishlatilmaydi'))
            return

        defaults = {**HERO_DEFAULTS}
        # PostHog har doim yoqiladi (seed --deploy shart emas).
        defaults['posthog_project_api_key'] = POSTHOG_KEY
        defaults['posthog_api_host'] = POSTHOG_HOST
        if deploy:
            defaults['ga4_measurement_id'] = GA4_ID

        LandingSettings.objects.update_or_create(pk=1, defaults=defaults)
        self.stdout.write(self.style.SUCCESS('LandingSettings yaratildi/yangilandi'))

        for order, (tab_key, label) in enumerate(PLATFORM_TABS):
            PlatformPreview.objects.update_or_create(
                tab=tab_key,
                defaults={
                    'title': label,
                    'order': order,
                    'is_active': True,
                    'alt_text': f'Ton Academy platform — {label}',
                },
            )
        self.stdout.write(self.style.SUCCESS(f'{len(PLATFORM_TABS)} ta platform preview tab'))

        for section, data in SECTION_COPY_DEFAULTS.items():
            LandingSectionCopy.objects.update_or_create(
                section=section,
                defaults={
                    'kicker': data['kicker'],
                    'title': data['title'],
                    'subtitle': data['subtitle'],
                    'is_active': True,
                },
            )
        self.stdout.write(self.style.SUCCESS(f'{len(SECTION_COPY_DEFAULTS)} ta section copy'))

        for order, proof in enumerate(HERO_PROOFS):
            LandingHeroProof.objects.update_or_create(
                order=order,
                defaults={
                    'icon': proof['icon'],
                    'title': proof['title'],
                    'subtitle': proof['subtitle'],
                    'is_active': True,
                },
            )
        self.stdout.write(self.style.SUCCESS(f'{len(HERO_PROOFS)} ta hero proof'))

        for order, card in enumerate(BENEFIT_CARDS):
            LandingBenefitCard.objects.update_or_create(
                order=order,
                defaults={
                    'icon': card['icon'],
                    'title': card['title'],
                    'text': card['text'],
                    'badge': card['badge'],
                    'is_active': True,
                },
            )
        self.stdout.write(self.style.SUCCESS(f'{len(BENEFIT_CARDS)} ta benefit card'))

        for order, card in enumerate(AI_CHECKER_CARDS):
            LandingAICard.objects.update_or_create(
                key=card['key'],
                defaults={
                    'icon': card['icon'],
                    'title': card['title'],
                    'text': card['text'],
                    'order': order,
                    'is_active': True,
                },
            )
        self.stdout.write(self.style.SUCCESS(f'{len(AI_CHECKER_CARDS)} ta AI card'))

        for step in PURCHASE_STEPS:
            ProcessStep.objects.update_or_create(
                flow='purchase',
                step_number=step['step_number'],
                defaults={
                    'title': step['title'],
                    'description': step['description'],
                    'icon': step['icon'],
                    'order': step['step_number'],
                    'is_active': True,
                },
            )
        self.stdout.write(self.style.SUCCESS(f'{len(PURCHASE_STEPS)} ta purchase step'))

        created_faq = 0
        updated_faq = 0
        for order, (question, answer) in enumerate(DEFAULT_FAQS, start=1):
            _, created = FAQ.objects.update_or_create(
                question=question,
                defaults={'answer': answer, 'order': order, 'is_active': True},
            )
            if created:
                created_faq += 1
            else:
                updated_faq += 1
        self.stdout.write(self.style.SUCCESS(f'FAQ: {created_faq} ta yangi, {updated_faq} ta yangilandi'))

        # Promo kartalar olib tashlangan — hech qachon qayta yoqilmaydi.
        offer_defaults = {
            'placement': 'current_offer',
            'campaign_id': 'live_sr_aug26',
            **LIVE_BUNDLE,
            'order': 0,
            'enabled': False,
        }
        ann_defaults = {
            'placement': 'announcement',
            'campaign_id': 'ann_live_sr_aug26',
            'title': 'Jonli darslar va website ga to‘liq access',
            'description': '',
            'price': 899_000,
            'cta_text': 'Batafsil',
            'cta_link': 'https://t.me/tonacademyuz',
            'badge': 'live',
            'order': 0,
            'enabled': False,
        }

        PromoCampaign.objects.update_or_create(
            campaign_id='live_sr_aug26',
            defaults=offer_defaults,
        )
        PromoCampaign.objects.update_or_create(
            campaign_id='ann_live_sr_aug26',
            defaults=ann_defaults,
        )
        self.stdout.write(self.style.SUCCESS('LIVE promo: o‘chiq (announcement + current_offer)'))

        if deploy:
            demo = seed_demo_social_proof()
            self.stdout.write(self.style.SUCCESS(
                f'Demo content: {demo["certificates"]} sertifikat, '
                f'{demo["students"]} o‘quvchi, {demo["testimonials"]} testimonial'
            ))
            self.stdout.write(self.style.SUCCESS(f'GA4 ID: {GA4_ID}'))
