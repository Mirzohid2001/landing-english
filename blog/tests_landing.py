from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from blog.models import FAQ, LandingSettings, PromoCampaign
from blog.services.landing import (
    BENEFIT_CARDS,
    HERO_PROOFS,
    SECTION_COPY_DEFAULTS,
    get_landing_context,
    normalize_purchase_steps,
)


class LandingSettingsTests(TestCase):
    def test_get_solo_creates_singleton(self):
        settings = LandingSettings.get_solo()
        self.assertEqual(settings.base_price, 599_000)
        self.assertEqual(LandingSettings.objects.count(), 1)
        self.assertIn('Kafolatlangan', settings.hero_headline)
        self.assertEqual(settings.primary_cta_text, 'Bepul daraja testini boshlash')

    def test_formatted_base_price(self):
        settings = LandingSettings.get_solo()
        self.assertEqual(settings.formatted_base_price(), '599 000')


class LandingServiceTests(TestCase):
    def test_benefit_cards_count(self):
        self.assertEqual(len(BENEFIT_CARDS), 6)
        self.assertEqual(len(HERO_PROOFS), 4)

    def test_purchase_steps_fallback(self):
        steps = normalize_purchase_steps()
        self.assertEqual(len(steps), 4)
        self.assertEqual(steps[0]['step_number'], 1)

    def test_get_landing_context_keys(self):
        context = get_landing_context()
        for key in (
            'landing',
            'benefit_cards',
            'ai_checker_cards',
            'hero_proofs',
            'section_copy',
            'purchase_steps',
            'platform_tabs',
            'faqs',
        ):
            self.assertIn(key, context)

    def test_section_copy_defaults_exposed(self):
        context = get_landing_context()
        self.assertEqual(context['section_copy']['platform']['kicker'], SECTION_COPY_DEFAULTS['platform']['kicker'])
        self.assertEqual(context['section_copy']['faq']['title'], SECTION_COPY_DEFAULTS['faq']['title'])

    def test_platform_tabs_has_six_items(self):
        tabs = get_landing_context()['platform_tabs']
        self.assertEqual(len(tabs), 6)
        self.assertEqual(tabs[0]['key'], 'all')


class PromoCampaignTests(TestCase):
    def test_expired_promo_not_active(self):
        promo = PromoCampaign.objects.create(
            enabled=True,
            placement='announcement',
            title='Expired promo',
            expires_at=timezone.now() - timedelta(hours=1),
        )
        self.assertFalse(promo.is_active_now)

    def test_active_promo_when_enabled(self):
        promo = PromoCampaign.objects.create(
            enabled=True,
            placement='current_offer',
            title='LIVE bundle',
            price=899_000,
        )
        self.assertTrue(promo.is_active_now)


class LandingPageTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        call_command('seed_landing')

    def test_home_page_status_ok(self):
        response = self.client.get(reverse('blog:home'))
        self.assertEqual(response.status_code, 200)

    def test_home_uses_landing_body_class(self):
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'landing-page')
        self.assertContains(response, 'landing.css')

    def test_home_pricing_card_without_visible_price(self):
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'lp-pricing-card')
        self.assertNotContains(response, 'lp-pricing-card__price')
        self.assertNotContains(response, 'lp-final-cta__price')
        self.assertNotContains(response, '599 000 so‘m')

    def test_home_has_telegram_purchase_cta(self):
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'Telegram orqali xarid qilish')
        self.assertContains(response, 'data-lp-track="hero_buy_click"')
        self.assertContains(response, 'data-lp-track="final_buy_click"')

    def test_home_has_mobile_sticky_cta(self):
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'id="lp-mobile-cta"')
        self.assertContains(response, 'data-lp-track="mobile_sticky_buy_click"')
        self.assertContains(response, 'lp-mobile-cta__btn')

    def test_home_primary_cta_is_free_level_test(self):
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'Bepul daraja testini boshlash')
        self.assertContains(response, 'data-lp-track="free_trial_click"')
        content = response.content.decode()
        primary_pos = content.find('lp-btn-primary')
        free_trial_pos = content.find('free_trial_click')
        telegram_pos = content.find('hero_buy_click')
        self.assertLess(primary_pos, telegram_pos)
        self.assertLess(free_trial_pos, telegram_pos)

    def test_home_hero_has_score_chips(self):
        response = self.client.get(reverse('blog:home'))
        content = response.content.decode()
        self.assertContains(response, 'lp-hero__score-row')
        self.assertContains(response, 'Natijalar')
        hero_start = content.find('lp-hero__score-row')
        hero_end = content.find('lp-hero__actions', hero_start)
        hero_scores = content[hero_start:hero_end]
        self.assertIn('lp-score-chip--7">7.0', hero_scores)
        self.assertIn('lp-score-chip--75">7.5', hero_scores)
        self.assertIn('lp-score-chip--8">8.0', hero_scores)
        self.assertIn('lp-hero__score-label">Natijalar', hero_scores)

    def test_home_removed_legacy_sections(self):
        response = self.client.get(reverse('blog:home'))
        self.assertNotContains(response, 'webinar-cta')
        self.assertNotContains(response, 'courses-section')
        self.assertNotContains(response, 'videos-section')
        self.assertNotContains(response, 'stats-section')

    def test_home_section_order(self):
        content = self.client.get(reverse('blog:home')).content.decode()
        hero_pos = content.find('lp-hero')
        platform_pos = content.find('id="platform"')
        benefits_pos = content.find('id="benefits"')
        ai_pos = content.find('id="ai-checker"')
        purchase_pos = content.find('id="purchase"')
        faq_pos = content.find('id="faq"')
        final_pos = content.find('lp-final-cta')
        self.assertLess(hero_pos, platform_pos)
        self.assertLess(platform_pos, benefits_pos)
        self.assertLess(benefits_pos, ai_pos)
        self.assertLess(ai_pos, purchase_pos)
        self.assertLess(purchase_pos, faq_pos)
        self.assertLess(faq_pos, final_pos)

    def test_home_has_six_benefit_cards(self):
        response = self.client.get(reverse('blog:home'))
        self.assertEqual(response.content.decode().count('class="lp-benefit-card"'), 6)

    def test_home_has_ai_checker_section(self):
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'AI checker qanday ishlaydi?')
        self.assertContains(response, 'lp-ai-card')
        self.assertContains(response, 'Writing AI')

    def test_ai_card_youtube_replaces_image(self):
        from blog.models import LandingAICard
        card = LandingAICard.objects.get(key='writing')
        card.video_url = 'https://www.youtube.com/watch?v=abcdefghijk'
        card.save()
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'youtube.com/embed/abcdefghijk')
        self.assertContains(response, 'lp-ai-card__video')

    def test_ai_card_uploaded_video_renders(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from blog.models import LandingAICard
        card = LandingAICard.objects.get(key='reading')
        card.video_file = SimpleUploadedFile('reading-demo.webm', b'webm', content_type='video/webm')
        card.save()
        response = self.client.get(reverse('blog:home'))
        content = response.content.decode()
        self.assertIn('<video', content)
        self.assertIn('data-lp-ai-video="reading"', content)
        self.assertIn('type="video/webm"', content)
        self.assertIn('landing/ai/', content)

    def test_platform_preview_has_single_stage(self):
        response = self.client.get(reverse('blog:home'))
        content = response.content.decode()
        self.assertContains(response, 'lp-preview__stage')
        self.assertEqual(content.count('lp-preview__stage'), 1)
        self.assertGreaterEqual(content.count('data-lp-panel='), 6)

    def test_certificates_carousel_renders_all_homepage_certs(self):
        from datetime import date
        from django.core.files.uploadedfile import SimpleUploadedFile
        from blog.models import IELTSCertificate

        IELTSCertificate.objects.all().delete()
        for i in range(8):
            IELTSCertificate.objects.create(
                student_name=f'Student {i}',
                ielts_score=7.0,
                date_obtained=date.today(),
                show_on_homepage=True,
                certificate_image=SimpleUploadedFile(
                    f'cert-{i}.png',
                    b'\x89PNG\r\n\x1a\n' + b'\x00' * 32,
                    content_type='image/png',
                ),
            )
        IELTSCertificate.objects.create(
            student_name='Hidden Cert',
            ielts_score=8.0,
            date_obtained=date.today(),
            show_on_homepage=False,
            certificate_image=SimpleUploadedFile(
                'hidden.png',
                b'\x89PNG\r\n\x1a\n' + b'\x00' * 32,
                content_type='image/png',
            ),
        )

        response = self.client.get(reverse('blog:home'))
        content = response.content.decode()
        self.assertContains(response, 'data-lp-carousel')
        self.assertContains(response, 'lp-carousel__track')
        self.assertEqual(content.count('lp-carousel__slide'), 8)
        self.assertNotContains(response, 'Hidden Cert')

    def test_home_has_purchase_flow_four_steps(self):
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'Qanday xarid qilinadi?')
        self.assertEqual(response.content.decode().count('lp-purchase-step lp-reveal'), 4)

    def test_home_faq_seeded(self):
        self.assertGreaterEqual(FAQ.objects.filter(is_active=True).count(), 9)
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'Bu oylik to‘lovmi?')
        self.assertContains(response, 'lp-faq__list')
        self.assertContains(response, 'lp-faq__question')
        self.assertNotContains(response, 'faq-section')

    def test_announcement_bar_when_promo_enabled(self):
        PromoCampaign.objects.create(
            enabled=True,
            placement='announcement',
            title='YANGI LIVE DASTUR',
            price=899_000,
            cta_link='https://t.me/tonacademyuz',
            campaign_id='test_ann',
        )
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'lp-announcement')
        self.assertContains(response, 'YANGI LIVE DASTUR')
        self.assertContains(response, 'has-announcement')

    def test_current_offer_hidden_when_disabled(self):
        PromoCampaign.objects.filter(placement='current_offer').update(enabled=False)
        PromoCampaign.objects.create(
            enabled=False,
            placement='current_offer',
            title='Hidden offer',
            price=899_000,
        )
        response = self.client.get(reverse('blog:home'))
        self.assertNotContains(response, 'lp-current-offer')

    def test_landing_js_included(self):
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'landing.js')

    def test_hero_headline_from_brief(self):
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'Kafolatlangan /')
        self.assertContains(response, 'IELTS - 7.0 + Online program')
        self.assertContains(
            response,
            'Britaniyalik ustozlar va kafolatlangan tizim orqali',
        )
        self.assertContains(response, '1000+')
        self.assertContains(response, 'Jonli darslar • Study plan')
        self.assertContains(response, 'Mobil + Desktop')
        self.assertContains(response, 'fas fa-users')

    def test_home_footer_has_social_links(self):
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'fab fa-instagram')
        self.assertContains(response, 'fab fa-youtube')
        self.assertContains(response, 'Dush–Shan')

    def test_home_has_purchase_track_connector(self):
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'lp-purchase__track')

    def test_home_has_section_analytics_attributes(self):
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'data-lp-section="platform"')
        self.assertContains(response, 'data-lp-section="results"')
        self.assertContains(response, 'data-lp-section="final-cta"')

    def test_seed_deploy_creates_demo_content(self):
        from blog.models import (
            IELTSCertificate,
            LandingAICard,
            LandingBenefitCard,
            LandingHeroProof,
            LandingSectionCopy,
            PlatformPreview,
            StudentResult,
            Testimonial,
        )
        call_command('seed_landing', '--deploy')
        self.assertEqual(PlatformPreview.objects.count(), 6)
        self.assertEqual(LandingSectionCopy.objects.count(), len(SECTION_COPY_DEFAULTS))
        self.assertEqual(LandingHeroProof.objects.count(), len(HERO_PROOFS))
        self.assertEqual(LandingBenefitCard.objects.count(), len(BENEFIT_CARDS))
        self.assertEqual(LandingAICard.objects.count(), 3)
        self.assertGreaterEqual(IELTSCertificate.objects.filter(show_on_homepage=True).count(), 4)
        self.assertGreaterEqual(StudentResult.objects.filter(is_featured=True).count(), 4)
        self.assertGreaterEqual(Testimonial.objects.filter(is_featured=True).count(), 4)
        settings = LandingSettings.get_solo()
        self.assertEqual(settings.ga4_measurement_id, 'G-6NKQ1LZYD0')
        self.assertTrue(settings.posthog_project_api_key.startswith('phc_'))
        self.assertIn('posthog.com', settings.posthog_api_host)

    def test_home_includes_posthog_snippet(self):
        call_command('seed_landing')
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'posthog.init')
        self.assertContains(response, 'phc_CBNfRo5dzYZE7zJK8VT5VwkvwyGdB8NJBEtjSP9YYYFT')
        self.assertContains(response, 'https://us.i.posthog.com')

    def test_home_platform_preview_has_images(self):
        call_command('seed_landing', '--deploy')
        response = self.client.get(reverse('blog:home'))
        self.assertContains(response, 'images/landing/platform-all-1200.webp')
        self.assertContains(response, 'images/landing/platform-writing-960.webp')
        self.assertContains(response, 'images/landing/planet-360.png')


class LandingInnerPageTests(TestCase):
    def setUp(self):
        self.client = Client()
        call_command('seed_landing')

    def _assert_landing_chrome(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'landing-page')
        self.assertContains(response, 'landing.css')
        self.assertContains(response, 'Telegram orqali xarid qilish')

    def test_videos_page_uses_landing_design(self):
        response = self.client.get(reverse('blog:videos'))
        self._assert_landing_chrome(response)
        self.assertContains(response, 'lp-page-hero')
        self.assertContains(response, 'lp-video-grid')
        self.assertContains(response, 'id="video-modal"')

    def test_students_page_uses_landing_design(self):
        response = self.client.get(reverse('blog:students'))
        self._assert_landing_chrome(response)
        self.assertContains(response, 'lp-student-grid')
        self.assertContains(response, 'lp-score-chip--7')

    def test_contact_page_uses_landing_design(self):
        response = self.client.get(reverse('blog:contact'))
        self._assert_landing_chrome(response)
        self.assertContains(response, 'lp-contact-grid')
        self.assertContains(response, 'id="contact-form"')
        self.assertContains(response, 'lp-input')

    def test_inner_pages_share_landing_nav(self):
        for url_name in ('blog:videos', 'blog:students', 'blog:contact', 'mock_tests:test_list'):
            response = self.client.get(reverse(url_name))
            self.assertContains(response, 'href="/#platform"')
            self.assertContains(response, 'href="/#faq"')

    def test_mock_tests_list_uses_landing_design(self):
        response = self.client.get(reverse('mock_tests:test_list'))
        self._assert_landing_chrome(response)
        self.assertContains(response, 'mock-landing')
        self.assertContains(response, 'mock-tests.css')
        self.assertContains(response, 'IELTS Mock Testlar')
        self.assertContains(response, 'mock-tests-grid')
