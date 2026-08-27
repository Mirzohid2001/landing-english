(function () {
    'use strict';

    function track(eventName, params) {
        const payload = { event: eventName, ...(params || {}) };
        window.dataLayer = window.dataLayer || [];
        window.dataLayer.push(payload);
        if (typeof window.gtag === 'function') {
            window.gtag('event', eventName, params || {});
        }
        if (window.posthog && typeof window.posthog.capture === 'function') {
            window.posthog.capture(eventName, params || {});
        }
    }

    function initPlatformTabs() {
        const root = document.querySelector('[data-lp-preview]');
        if (!root) return;

        const tabs = root.querySelectorAll('[data-lp-tab]');
        const panels = root.querySelectorAll('[data-lp-panel]');
        if (!tabs.length) return;

        tabs.forEach((tab) => {
            tab.addEventListener('click', () => {
                const key = tab.getAttribute('data-lp-tab');
                tabs.forEach((t) => t.classList.toggle('is-active', t === tab));
                panels.forEach((panel) => {
                    panel.hidden = panel.getAttribute('data-lp-panel') !== key;
                });
                track('platform_demo_view', { tab: key });
            });
        });
    }

    function initCtaTracking() {
        document.querySelectorAll('[data-lp-track]').forEach((el) => {
            el.addEventListener('click', () => {
                const eventName = el.getAttribute('data-lp-track');
                const params = {
                    offer_type: el.getAttribute('data-offer-type') || '',
                    offer_price: el.getAttribute('data-offer-price') || '',
                    campaign_id: el.getAttribute('data-campaign-id') || '',
                };
                track(eventName, params);
        if (['hero_buy_click', 'final_buy_click', 'header_buy_click', 'current_offer_click', 'announcement_click', 'contact_buy_click', 'mobile_sticky_buy_click'].includes(eventName) || (eventName && eventName.includes('telegram'))) {
                    track('telegram_click', params);
                }
                if (params.campaign_id) {
                    track('campaign_telegram_click', params);
                }
            });
        });
    }

    function initScrollDepth() {
        const marks = [25, 50, 75, 90];
        const fired = new Set();
        window.addEventListener('scroll', () => {
            const doc = document.documentElement;
            const max = doc.scrollHeight - window.innerHeight;
            if (max <= 0) return;
            const pct = Math.round((window.scrollY / max) * 100);
            marks.forEach((mark) => {
                if (pct >= mark && !fired.has(mark)) {
                    fired.add(mark);
                    track(`scroll_${mark}`);
                }
            });
        }, { passive: true });
    }

    function initSectionViews() {
        const sectionEvents = {
            announcement: 'announcement_view',
            'current-offer': 'current_offer_view',
            platform: 'platform_section_view',
            benefits: 'benefits_view',
            'ai-checker': 'ai_checker_view',
            results: 'student_results_view',
            testimonials: 'testimonials_view',
            news: 'news_section_view',
            purchase: 'purchase_flow_view',
            faq: 'faq_section_view',
            'final-cta': 'final_cta_view',
        };

        const seen = new Set();
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                const key = entry.target.getAttribute('data-lp-section');
                if (!key || seen.has(key)) return;
                seen.add(key);
                const eventName = sectionEvents[key];
                if (eventName) {
                    track(eventName, { section: key });
                }
            });
        }, { threshold: 0.25 });

        document.querySelectorAll('[data-lp-section]').forEach((el) => observer.observe(el));
    }

    function initAiCardViews() {
        const aiEvents = {
            writing: 'writing_ai_view',
            reading: 'reading_ai_view',
            listening: 'listening_ai_view',
        };
        const seen = new Set();
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                const key = entry.target.getAttribute('data-lp-ai');
                if (!key || seen.has(key)) return;
                seen.add(key);
                const eventName = aiEvents[key];
                if (eventName) track(eventName, { ai_type: key });
            });
        }, { threshold: 0.35 });

        document.querySelectorAll('[data-lp-ai]').forEach((el) => observer.observe(el));
    }

    function initScrollReveal() {
        const items = document.querySelectorAll('.lp-reveal');
        if (!items.length) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

        items.forEach((el, index) => {
            el.style.transitionDelay = `${Math.min(index % 6, 5) * 70}ms`;
            observer.observe(el);
        });
    }

    function initFaqAccordion() {
        document.querySelectorAll('.lp-faq__question').forEach((button) => {
            button.addEventListener('click', () => {
                const item = button.closest('.lp-faq__item');
                const answer = item?.querySelector('.lp-faq__answer');
                if (!item || !answer) return;

                const willOpen = !item.classList.contains('is-open');
                item.classList.toggle('is-open', willOpen);
                button.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
                answer.hidden = !willOpen;

                if (willOpen) {
                    track('faq_open');
                }
            });
        });
    }

    function initTestimonialTracking() {
        document.querySelectorAll('[data-testimonial-id]').forEach((el) => {
            el.addEventListener('click', () => {
                track('testimonial_play', {
                    testimonial_id: el.getAttribute('data-testimonial-id') || '',
                });
            });
        });
    }

    function initMobileStickyCta() {
        const bar = document.getElementById('lp-mobile-cta');
        if (!bar) return;

        const hero = document.querySelector('.lp-hero, .lp-page-hero');
        const finalCta = document.querySelector('[data-lp-section="final-cta"], .lp-final-cta');
        const mq = window.matchMedia('(max-width: 767px)');

        function update() {
            if (!mq.matches) {
                bar.hidden = true;
                document.body.classList.remove('lp-sticky-cta-visible');
                return;
            }

            const pastHero = hero
                ? window.scrollY > hero.offsetTop + hero.offsetHeight * 0.55
                : window.scrollY > 320;

            let nearFinal = false;
            if (finalCta) {
                const rect = finalCta.getBoundingClientRect();
                nearFinal = rect.top < window.innerHeight - 72;
            }

            const show = pastHero && !nearFinal;
            bar.hidden = !show;
            document.body.classList.toggle('lp-sticky-cta-visible', show);
        }

        window.addEventListener('scroll', update, { passive: true });
        window.addEventListener('resize', update);
        if (mq.addEventListener) {
            mq.addEventListener('change', update);
        }
        update();
    }

    document.addEventListener('DOMContentLoaded', () => {
        initPlatformTabs();
        initCtaTracking();
        initScrollDepth();
        initSectionViews();
        initAiCardViews();
        initScrollReveal();
        initFaqAccordion();
        initTestimonialTracking();
        initMobileStickyCta();
    });
})();
