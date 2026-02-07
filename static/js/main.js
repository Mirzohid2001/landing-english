// Performance optimization utilities
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Get CSRF token for AJAX requests
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getCsrfToken() {
    return getCookie('csrftoken');
}

// Utility Functions
function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
        setTimeout(() => {
            overlay.style.display = 'none';
        }, 500);
    }
}

// Toast Notification Function
function showToast(message, type = 'success', title = '') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        info: 'fas fa-info-circle'
    };
    
    const titles_default = {
        success: 'Muvaffaqiyatli!',
        error: 'Xatolik!',
        info: 'Ma\'lumot'
    };
    
    toast.innerHTML = `
        <i class="${icons[type] || icons.info} toast-icon"></i>
        <div class="toast-content">
            ${title ? `<div class="toast-title">${title}</div>` : ''}
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" aria-label="Close">&times;</button>
    `;
    
    container.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Auto remove after 5 seconds
    const autoRemove = setTimeout(() => {
        removeToast(toast);
    }, 5000);
    
    // Close button functionality
    toast.querySelector('.toast-close').addEventListener('click', () => {
        clearTimeout(autoRemove);
        removeToast(toast);
    });
}

function removeToast(toast) {
    toast.classList.remove('show');
    setTimeout(() => {
        toast.remove();
    }, 400);
}

// Legacy function for compatibility
function showAlert(message, type = 'success') {
    showToast(message, type);
}

function createMessagesContainer() {
    const container = document.createElement('div');
    container.className = 'messages-container';
    document.body.appendChild(container);
    return container;
}

// Modal functionality
document.addEventListener('DOMContentLoaded', function() {
    // Close modal when clicking outside
    window.onclick = function(event) {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    }
    
    // Close modal buttons
    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', function() {
            this.closest('.modal').style.display = 'none';
        });
    });
    
    // Mobile menu toggle
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            this.classList.toggle('active');
        });
    }
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Application form handling (if exists on page)
    const applicationForm = document.getElementById('application-form');
    if (applicationForm) {
        applicationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const form = this;
            const formData = new FormData(form);
            
            showLoading();
            
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCsrfToken(),
                }
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                if (data.success) {
                    showToast(data.message, 'success', 'Ariza Yuborildi!');
                    form.reset();
                    const modal = form.closest('.modal');
                    if (modal) {
                        modal.style.display = 'none';
                    }
                } else {
                    let errorMessage = 'Please check the form and try again.';
                    if (data.errors) {
                        errorMessage = Object.values(data.errors).flat().join(', ');
                    }
                    showToast(errorMessage, 'error', 'Error');
                }
            })
            .catch(error => {
                hideLoading();
                showAlert('Xatolik yuz berdi. Iltimos, qayta urinib ko\'ring.', 'error');
                console.error('Error:', error);
            });
        });
    }
    
    // Contact form handling (if exists on page)
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const form = this;
            const formData = new FormData(form);
            
            showLoading();
            
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCsrfToken(),
                }
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                if (data.success) {
                    showToast(data.message, 'success', 'Xabar Yuborildi!');
                    form.reset();
                } else {
                    let errorMessage = 'Please check the form and try again.';
                    if (data.errors) {
                        errorMessage = Object.values(data.errors).flat().join(', ');
                    }
                    showToast(errorMessage, 'error', 'Error');
                }
            })
            .catch(error => {
                hideLoading();
                showAlert('Xatolik yuz berdi. Iltimos, qayta urinib ko\'ring.', 'error');
                console.error('Error:', error);
            });
        });
    }
    
    // Apply course buttons
    document.querySelectorAll('.apply-course-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const courseId = this.getAttribute('data-course-id');
            const modal = document.getElementById('application-modal');
            const courseInput = document.getElementById('application-course-id');
            
            if (modal && courseInput) {
                courseInput.value = courseId;
                modal.style.display = 'block';
            }
        });
    });
});

// Navbar scroll effect - оптимизировано с throttle
const handleNavbarScroll = throttle(() => {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
}, 100);

window.addEventListener('scroll', handleNavbarScroll, { passive: true });

// Scroll animations - улучшенная версия с более ранним появлением
const observerOptions = {
    threshold: 0.01,
    rootMargin: '0px 0px 400px 0px' // Элементы появляются на 400px раньше
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const target = entry.target;
            target.style.opacity = '1';
            target.style.transform = 'translate3d(0, 0, 0)';
            // Убираем will-change после анимации для производительности
            setTimeout(() => {
                target.style.willChange = 'auto';
            }, 500);
            // Убираем наблюдение после появления для производительности
            observer.unobserve(target);
        }
    });
}, observerOptions);

// Observe elements for scroll animations - оптимизированная версия
document.addEventListener('DOMContentLoaded', function() {
    const animateElements = document.querySelectorAll('.course-card, .teacher-card, .feature-card, .testimonial-card, .certificate-card, .faq-item, .timeline-item, .stat-card, .partner-item, .benefit-card');
    
    animateElements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translate3d(0, 20px, 0)';
        el.style.transition = `opacity 0.4s ease ${index * 0.03}s, transform 0.4s ease ${index * 0.03}s`;
        el.style.willChange = 'transform, opacity';
        el.style.contain = 'layout style paint';
        observer.observe(el);
    });
});

// Lazy loading images
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                }
                observer.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
}

// Create animated particles - оптимизированная версия с адаптивностью
function createParticles() {
    const particlesContainer = document.getElementById('particles');
    if (!particlesContainer) return;
    
    // Адаптивное количество частиц в зависимости от устройства
    const isMobile = window.innerWidth < 768;
    const isTablet = window.innerWidth < 1024 && window.innerWidth >= 768;
    const particleCount = isMobile ? 10 : (isTablet ? 15 : 20);
    
    // Используем DocumentFragment для оптимизации
    const fragment = document.createDocumentFragment();
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        // Random position
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 20 + 's';
        particle.style.animationDuration = (15 + Math.random() * 10) + 's';
        
        // Random size (smaller)
        const size = isMobile ? (1 + Math.random()) : (2 + Math.random() * 2);
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        
        // GPU acceleration
        particle.style.transform = 'translateZ(0)';
        particle.style.willChange = 'transform';
        particle.style.backfaceVisibility = 'hidden';
        particle.style.contain = 'layout style paint';
        
        // Softer colors
        const colors = [
            'rgba(255, 255, 255, 0.3)',
            'rgba(37, 99, 235, 0.25)',
            'rgba(245, 158, 11, 0.25)',
            'rgba(16, 185, 129, 0.25)',
            'rgba(59, 130, 246, 0.25)'
        ];
        const color = colors[Math.floor(Math.random() * colors.length)];
        particle.style.background = color;
        if (!isMobile) {
            particle.style.boxShadow = `0 0 ${size * 1.5}px ${color}`;
        }
        
        fragment.appendChild(particle);
    }
    
    particlesContainer.appendChild(fragment);
}

// Initialize particles on page load
document.addEventListener('DOMContentLoaded', function() {
    // Задержка для улучшения первоначальной загрузки
    setTimeout(createParticles, 100);
});

// Parallax effect for hero section - оптимизированная версия
let lastScrollY = 0;
let ticking = false;
let shapes = null;
let hero = null;

// Кешируем элементы один раз
document.addEventListener('DOMContentLoaded', function() {
    hero = document.querySelector('.hero');
    if (hero) {
        shapes = hero.querySelectorAll('.shape');
    }
});

function updateParallax() {
    if (!hero || !shapes) {
        ticking = false;
        return;
    }
    
    const scrolled = window.pageYOffset;
    
    // Отключаем parallax на мобильных для производительности
    if (window.innerWidth < 768 || scrolled >= window.innerHeight) {
        ticking = false;
        return;
    }
    
    // Оптимизированный parallax только для первых 4 shapes
    const maxShapes = Math.min(shapes.length, 4);
    for (let i = 0; i < maxShapes; i++) {
        const shape = shapes[i];
        const speed = 0.2 + (i % 3) * 0.05;
        const yPos = -(scrolled * speed);
        shape.style.transform = `translate3d(0, ${yPos}px, 0)`;
    }
    
    ticking = false;
}

const handleParallax = throttle(() => {
    if (!ticking) {
        window.requestAnimationFrame(updateParallax);
        ticking = true;
    }
}, 16);

window.addEventListener('scroll', handleParallax, { passive: true });

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const offsetTop = target.offsetTop - 80;
            window.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
        }
    });
});

// Animated counters for stats
function animateCounter(element) {
    const target = parseInt(element.getAttribute('data-target'));
    const duration = 2000;
    const increment = target / (duration / 16);
    let current = 0;
    
    const updateCounter = () => {
        current += increment;
        if (current < target) {
            element.textContent = Math.floor(current);
            requestAnimationFrame(updateCounter);
        } else {
            element.textContent = target;
        }
    };
    
    updateCounter();
}

// Intersection Observer for stats animation
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const statNumbers = entry.target.querySelectorAll('.stat-number');
            statNumbers.forEach(stat => {
                if (!stat.classList.contains('animated')) {
                    stat.classList.add('animated');
                    animateCounter(stat);
                }
            });
        }
    });
}, { threshold: 0.5 });

// Observe stats section
document.addEventListener('DOMContentLoaded', function() {
    const statsSection = document.querySelector('.stats-section');
    if (statsSection) {
        statsObserver.observe(statsSection);
    }
});

// Preloader - скрытие после загрузки
window.addEventListener('load', function() {
    setTimeout(() => {
        hideLoading();
    }, 800);
});

// Scroll Progress Bar - оптимизировано
document.addEventListener('DOMContentLoaded', function() {
    const progressBar = document.getElementById('scroll-progress-bar');
    if (!progressBar) return;
    
    const updateProgress = throttle(() => {
        const windowHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = (window.pageYOffset / windowHeight) * 100;
        progressBar.style.width = scrolled + '%';
    }, 16);
    
    window.addEventListener('scroll', updateProgress, { passive: true });
});

// Scroll to Top Button - оптимизировано
document.addEventListener('DOMContentLoaded', function() {
    const scrollToTopBtn = document.getElementById('scroll-to-top');
    
    if (!scrollToTopBtn) return;
    
    // Показываем/скрываем кнопку при скролле с throttle
    const handleScrollToTop = throttle(() => {
        if (window.pageYOffset > 300) {
            scrollToTopBtn.classList.add('visible');
        } else {
            scrollToTopBtn.classList.remove('visible');
        }
    }, 150);
    
    window.addEventListener('scroll', handleScrollToTop, { passive: true });
    
    // Плавная прокрутка наверх при клике
    scrollToTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
});

// Typing Effect for Hero Title
document.addEventListener('DOMContentLoaded', function() {
    const heroTitle = document.querySelector('.hero-title');
    if (!heroTitle) return;
    
    const titleLines = heroTitle.querySelectorAll('.title-line-1, .title-line-2');
    if (titleLines.length === 0) return;
    
    titleLines.forEach((line, index) => {
        const originalText = line.textContent;
        line.textContent = '';
        line.style.opacity = '1';
        
        setTimeout(() => {
            let charIndex = 0;
            const typeChar = () => {
                if (charIndex < originalText.length) {
                    line.textContent += originalText.charAt(charIndex);
                    charIndex++;
                    setTimeout(typeChar, 50);
                }
            };
            typeChar();
        }, index * 1000);
    });
});

// Ripple Effect for Cards
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.course-card, .feature-card, .teacher-card, .testimonial-card, .certificate-card, .benefit-card');
    
    cards.forEach(card => {
        card.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
});

// Certificates Slider with Auto-play
document.addEventListener('DOMContentLoaded', function() {
    const sliderWrapper = document.querySelector('.certificates-slider-wrapper');
    if (!sliderWrapper) return;
    
    const sliderTrack = sliderWrapper.querySelector('.certificates-slider-track');
    const sliderItems = sliderWrapper.querySelectorAll('.certificate-card.slider-item');
    const prevBtn = sliderWrapper.querySelector('.slider-btn-prev');
    const nextBtn = sliderWrapper.querySelector('.slider-btn-next');
    const indicators = sliderWrapper.querySelectorAll('.slider-indicator');
    
    if (!sliderTrack || sliderItems.length === 0) return;
    
    let currentIndex = 0;
    let autoPlayInterval;
    const autoPlayDelay = 6000; // 6 секунд между слайдами (медленнее)
    let isPaused = false;
    
    // Функция для обновления слайдера
    function updateSlider(index) {
        // Ограничиваем индекс
        if (index < 0) {
            currentIndex = sliderItems.length - 1;
        } else if (index >= sliderItems.length) {
            currentIndex = 0;
        } else {
            currentIndex = index;
        }
        
        // Вычисляем смещение для центрирования активной карточки
        const sliderWidth = sliderWrapper.querySelector('.certificates-slider').offsetWidth;
        const itemWidth = sliderItems[0].offsetWidth;
        const gap = 28.8; // 1.8rem = 28.8px
        const totalItemWidth = itemWidth + gap;
        
        // Центрируем активную карточку
        const offset = (sliderWidth / 2) - (itemWidth / 2) - (currentIndex * totalItemWidth);
        
        // Применяем трансформацию с плавным переходом
        sliderTrack.style.transition = 'transform 1.2s cubic-bezier(0.4, 0, 0.2, 1)';
        sliderTrack.style.transform = `translate3d(${offset}px, 0, 0)`;
        
        // Обновляем активные классы
        sliderItems.forEach((item, i) => {
            if (i === currentIndex) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
        
        // Обновляем индикаторы
        indicators.forEach((indicator, i) => {
            if (i === currentIndex) {
                indicator.classList.add('active');
            } else {
                indicator.classList.remove('active');
            }
        });
        
        // Обновляем состояние кнопок
        if (prevBtn) {
            prevBtn.disabled = sliderItems.length <= 1;
        }
        if (nextBtn) {
            nextBtn.disabled = sliderItems.length <= 1;
        }
    }
    
    // Функция для следующего слайда
    function nextSlide() {
        updateSlider(currentIndex + 1);
    }
    
    // Функция для предыдущего слайда
    function prevSlide() {
        updateSlider(currentIndex - 1);
    }
    
    // Функция для запуска автоплея
    function startAutoPlay() {
        // Останавливаем предыдущий интервал, если есть
        stopAutoPlay();
        
        // Проверяем, что есть элементы для прокрутки
        if (sliderItems.length <= 1) {
            return;
        }
        
        // Сбрасываем флаг паузы на всякий случай
        isPaused = false;
        
        // Запускаем новый интервал
        autoPlayInterval = setInterval(() => {
            if (!isPaused && sliderItems.length > 1) {
                nextSlide();
            }
        }, autoPlayDelay);
    }
    
    // Функция для остановки автоплея
    function stopAutoPlay() {
        if (autoPlayInterval) {
            clearInterval(autoPlayInterval);
            autoPlayInterval = null;
        }
    }
    
    // Обработчики для кнопок навигации
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            nextSlide();
            stopAutoPlay();
            startAutoPlay();
        });
    }
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            prevSlide();
            stopAutoPlay();
            startAutoPlay();
        });
    }
    
    // Обработчики для индикаторов
    indicators.forEach((indicator, index) => {
        indicator.addEventListener('click', () => {
            updateSlider(index);
            stopAutoPlay();
            startAutoPlay();
        });
    });
    
    // Пауза при наведении мыши
    sliderWrapper.addEventListener('mouseenter', () => {
        isPaused = true;
    });
    
    sliderWrapper.addEventListener('mouseleave', () => {
        isPaused = false;
        // Перезапускаем автоплей при уходе мыши, если он был остановлен
        if (!autoPlayInterval && sliderItems.length > 1) {
            startAutoPlay();
        }
    });
    
    // Обработка изменения размера окна
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            updateSlider(currentIndex);
        }, 250);
    });
    
    // Инициализация слайдера
    function initSlider() {
        if (sliderItems.length === 0) {
            return;
        }
        
        // Устанавливаем начальную позицию
        updateSlider(0);
        
        // Запускаем автоплей после небольшой задержки
        setTimeout(() => {
            startAutoPlay();
        }, 800);
    }
    
    // Инициализируем сразу, так как DOMContentLoaded уже произошел
    setTimeout(initSlider, 500);
    
    // Остановка автоплея при потере фокуса страницы
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            stopAutoPlay();
        } else {
            setTimeout(() => {
                if (sliderItems.length > 1) {
                    startAutoPlay();
                }
            }, 300);
        }
    });
    
    // Дополнительная проверка при полной загрузке страницы
    window.addEventListener('load', () => {
        setTimeout(() => {
            if (!autoPlayInterval && sliderItems.length > 1) {
                startAutoPlay();
            }
        }, 1500);
    });
});

