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

        const tabs = Array.from(root.querySelectorAll('[data-lp-tab]'));
        const panels = Array.from(root.querySelectorAll('[data-lp-panel]'));
        if (!tabs.length || !panels.length) return;

        function activate(key) {
            tabs.forEach((tab) => {
                const active = tab.getAttribute('data-lp-tab') === key;
                tab.classList.toggle('is-active', active);
                tab.setAttribute('aria-selected', active ? 'true' : 'false');
                tab.tabIndex = active ? 0 : -1;
            });
            panels.forEach((panel) => {
                const active = panel.getAttribute('data-lp-panel') === key;
                panel.classList.toggle('is-active', active);
                if (active) {
                    panel.removeAttribute('hidden');
                } else {
                    panel.setAttribute('hidden', '');
                }
            });
        }

        tabs.forEach((tab) => {
            tab.addEventListener('click', () => {
                const key = tab.getAttribute('data-lp-tab');
                if (!key) return;
                activate(key);
                track('platform_demo_view', { tab: key });
            });
        });

        root.addEventListener('keydown', (event) => {
            const current = tabs.findIndex((t) => t.classList.contains('is-active'));
            if (current < 0) return;
            let next = current;
            if (event.key === 'ArrowRight') next = (current + 1) % tabs.length;
            else if (event.key === 'ArrowLeft') next = (current - 1 + tabs.length) % tabs.length;
            else if (event.key === 'Home') next = 0;
            else if (event.key === 'End') next = tabs.length - 1;
            else return;
            event.preventDefault();
            const key = tabs[next].getAttribute('data-lp-tab');
            activate(key);
            tabs[next].focus();
            track('platform_demo_view', { tab: key });
        });

        const initial = tabs.find((t) => t.classList.contains('is-active')) || tabs[0];
        activate(initial.getAttribute('data-lp-tab'));
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

    function initAiVideos() {
        const videos = Array.from(document.querySelectorAll('[data-lp-ai-video]'));
        if (!videos.length) return;

        videos.forEach((video) => {
            video.addEventListener('play', () => {
                videos.forEach((other) => {
                    if (other !== video && !other.paused) {
                        other.pause();
                    }
                });
                track('ai_video_play', {
                    ai_type: video.getAttribute('data-lp-ai-video') || '',
                });
            });
        });
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

    function initCertificateCarousel() {
        const root = document.querySelector('[data-lp-carousel]');
        if (!root) return;

        const viewport = root.querySelector('[data-lp-carousel-viewport]');
        const track = root.querySelector('[data-lp-carousel-track]');
        const prevBtn = root.querySelector('[data-lp-carousel-prev]');
        const nextBtn = root.querySelector('[data-lp-carousel-next]');
        const dotsWrap = root.querySelector('[data-lp-carousel-dots]');
        if (!viewport || !track) return;

        const originalSlides = Array.from(track.querySelectorAll('.lp-carousel__slide'));
        if (!originalSlides.length) return;

        if (dotsWrap) dotsWrap.hidden = true;

        if (originalSlides.length <= 1) {
            if (prevBtn) prevBtn.hidden = true;
            if (nextBtn) nextBtn.hidden = true;
            return;
        }

        // Infinite strip: continuous marquee via transform + cloned sets.
        const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        const canHover = window.matchMedia('(hover: hover)').matches;
        let offset = 0;
        let paused = false;
        let pointerDown = false;
        let loopWidth = 0;
        let rafId = 0;
        let lastTs = 0;
        const speed = 42; // px / second

        function measureGap() {
            const style = window.getComputedStyle(track);
            return parseFloat(style.columnGap || style.gap || '16') || 16;
        }

        function slideWidth() {
            const first = track.querySelector('.lp-carousel__slide');
            if (!first) return 260;
            return first.getBoundingClientRect().width + measureGap();
        }

        function syncPaused() {
            const focused = root.contains(document.activeElement);
            paused = pointerDown || focused || (canHover && root.matches(':hover'));
            if (!paused) lastTs = 0;
        }

        function ensureLoopCopies() {
            if (!track.dataset.lpCloned) {
                const markup = originalSlides.map((slide) => {
                    const node = slide.cloneNode(true);
                    node.setAttribute('aria-hidden', 'true');
                    node.querySelectorAll('img').forEach((img) => {
                        img.setAttribute('loading', 'lazy');
                        img.removeAttribute('fetchpriority');
                    });
                    return node.outerHTML;
                }).join('');
                // Two extra sets so wide viewports never show empty space.
                track.insertAdjacentHTML('beforeend', markup + markup);
                track.dataset.lpCloned = '1';
            }

            const all = track.querySelectorAll('.lp-carousel__slide');
            const count = originalSlides.length;
            if (!count || all.length < count) {
                loopWidth = 0;
                return;
            }

            // Distance from start of set N to start of set N+1 includes the gap
            // after the last slide (flex gap between sets).
            let width = 0;
            for (let i = 0; i < count; i += 1) {
                width += all[i].getBoundingClientRect().width;
            }
            width += measureGap() * count;
            loopWidth = width;
        }

        function applyTransform() {
            track.style.transform = `translate3d(${-offset}px, 0, 0)`;
        }

        function tick(ts) {
            if (!lastTs) lastTs = ts;
            const delta = Math.min(48, ts - lastTs);
            lastTs = ts;

            if (!paused && !reduceMotion && !document.hidden && loopWidth > 0) {
                offset += (speed * delta) / 1000;
                if (offset >= loopWidth) {
                    offset %= loopWidth;
                }
                applyTransform();
            }

            rafId = window.requestAnimationFrame(tick);
        }

        function jumpBy(dir) {
            if (!loopWidth) return;
            const step = slideWidth();
            offset += dir * step;
            offset = ((offset % loopWidth) + loopWidth) % loopWidth;
            applyTransform();
        }

        function recalc() {
            const prev = offset;
            const prevLoop = loopWidth || 1;
            ensureLoopCopies();
            if (loopWidth > 0) {
                offset = (prev / prevLoop) * loopWidth;
                offset %= loopWidth;
            }
            applyTransform();
        }

        root.classList.add('is-autoplay');
        track.style.overflow = 'visible';
        track.scrollLeft = 0;

        if (prevBtn) {
            prevBtn.disabled = false;
            prevBtn.addEventListener('click', () => jumpBy(-1));
        }
        if (nextBtn) {
            nextBtn.disabled = false;
            nextBtn.addEventListener('click', () => jumpBy(1));
        }

        if (canHover) {
            root.addEventListener('mouseenter', syncPaused);
            root.addEventListener('mouseleave', syncPaused);
        }
        root.addEventListener('focusin', syncPaused);
        root.addEventListener('focusout', () => {
            window.setTimeout(syncPaused, 0);
        });
        root.addEventListener('pointerdown', () => {
            pointerDown = true;
            syncPaused();
        }, { passive: true });
        window.addEventListener('pointerup', () => {
            pointerDown = false;
            syncPaused();
        }, { passive: true });
        window.addEventListener('pointercancel', () => {
            pointerDown = false;
            syncPaused();
        }, { passive: true });

        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) lastTs = 0;
        });

        let resizeTimer = null;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = window.setTimeout(recalc, 120);
        });

        // Images can change slide widths after first paint — remeasure.
        track.querySelectorAll('img').forEach((img) => {
            if (img.complete) return;
            img.addEventListener('load', recalc, { once: true });
            img.addEventListener('error', recalc, { once: true });
        });

        window.requestAnimationFrame(() => {
            ensureLoopCopies();
            applyTransform();
            if (!reduceMotion) {
                rafId = window.requestAnimationFrame(tick);
            }
        });

        window.addEventListener('beforeunload', () => {
            if (rafId) window.cancelAnimationFrame(rafId);
        }, { once: true });
    }

    document.addEventListener('DOMContentLoaded', () => {
        initPlatformTabs();
        initCtaTracking();
        initScrollDepth();
        initSectionViews();
        initAiCardViews();
        initAiVideos();
        initScrollReveal();
        initFaqAccordion();
        initTestimonialTracking();
        initMobileStickyCta();
        initCertificateCarousel();
    });
})();
