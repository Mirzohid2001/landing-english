from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse


class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('elementary', 'Elementary'),
        ('intermediate', 'Intermediate'),
        ('upper-intermediate', 'Upper-Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.CharField(max_length=100, help_text="e.g., '3 months', '6 weeks'")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    image = models.ImageField(upload_to='courses/', blank=True, null=True)
    promo_video_file = models.FileField(upload_to='videos/courses/', blank=True, null=True, help_text="Local video file only")
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('course_detail', kwargs={'pk': self.pk})


class Teacher(models.Model):
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='teachers/', blank=True, null=True)
    bio = models.TextField()
    specialization = models.CharField(max_length=200)
    experience = models.IntegerField(help_text="Years of experience")
    video_file = models.FileField(upload_to='videos/teachers/', blank=True, null=True, help_text="Local video file only")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Testimonial(models.Model):
    RATING_CHOICES = [
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    ]
    
    student_name = models.CharField(max_length=100)
    student_photo = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    text = models.TextField()
    rating = models.IntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='testimonials')
    video_file = models.FileField(upload_to='videos/testimonials/', blank=True, null=True, help_text="Local video file only")
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student_name} - {self.rating} stars"


class Video(models.Model):
    VIDEO_TYPE_CHOICES = [
        ('course_lesson', 'Course Lesson'),
        ('promo', 'Promo Video'),
        ('testimonial', 'Testimonial'),
        ('about', 'About School'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_url = models.URLField(blank=True, null=True, help_text="YouTube or Vimeo URL")
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    video_type = models.CharField(max_length=20, choices=VIDEO_TYPE_CHOICES)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='lesson_videos')
    preview_image = models.ImageField(upload_to='video_previews/', blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return self.title


class ContactRequest(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d')}"


class CourseApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('contacted', 'Contacted'),
        ('enrolled', 'Enrolled'),
        ('rejected', 'Rejected'),
    ]
    
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.course.title}"


class About(models.Model):
    title = models.CharField(max_length=200, default="About Our School")
    text = models.TextField()
    mission = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    video_file = models.FileField(upload_to='videos/about/', blank=True, null=True, help_text="Local video file only")
    image = models.ImageField(upload_to='about/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "About"
    
    def __str__(self):
        return self.title


class Feature(models.Model):
    icon = models.CharField(max_length=100, help_text="Font Awesome icon class or emoji")
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.title


class IELTSCertificate(models.Model):
    student_name = models.CharField(max_length=100)
    student_photo = models.ImageField(upload_to='certificates/students/', blank=True, null=True)
    ielts_score = models.DecimalField(max_digits=3, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(9)])
    certificate_image = models.ImageField(upload_to='certificates/')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='certificates')
    date_obtained = models.DateField()
    show_on_homepage = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_obtained', '-ielts_score']
        verbose_name = 'IELTS sertifikat'
        verbose_name_plural = 'IELTS sertifikatlar'
    
    def __str__(self):
        return f"{self.student_name} - IELTS {self.ielts_score}"


class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.IntegerField(default=0, help_text="Order in which FAQ appears (lower numbers first)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQ savollar'
    
    def __str__(self):
        return self.question


class ProcessStep(models.Model):
    FLOW_CHOICES = [
        ('general', 'Umumiy'),
        ('purchase', 'Telegram xarid'),
    ]

    ICON_CHOICES = [
        ('fas fa-user-plus', 'Sign Up'),
        ('fas fa-clipboard-check', 'Assessment'),
        ('fas fa-chalkboard-teacher', 'Learn'),
        ('fas fa-trophy', 'Excel'),
        ('fas fa-book', 'Book'),
        ('fas fa-certificate', 'Certificate'),
        ('fas fa-users', 'Users'),
        ('fas fa-graduation-cap', 'Graduation'),
        ('fab fa-telegram-plane', 'Telegram'),
        ('fas fa-comments', 'Comments'),
        ('fas fa-credit-card', 'Payment'),
        ('fas fa-key', 'Key'),
    ]
    
    step_number = models.IntegerField(help_text="Step number (1, 2, 3, 4, etc.)")
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=100, help_text="Font Awesome icon class, masalan: fas fa-key")
    flow = models.CharField(max_length=20, choices=FLOW_CHOICES, default='general')
    order = models.IntegerField(default=0, help_text="Order in which step appears (lower numbers first)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'step_number']
        verbose_name = "Process Step"
        verbose_name_plural = "Process Steps"
    
    def __str__(self):
        return f"Step {self.step_number}: {self.title}"


class StudentResult(models.Model):
    """O'quvchilarning natijalari va ma'lumotlari"""
    first_name = models.CharField(max_length=100, verbose_name="Ism")
    last_name = models.CharField(max_length=100, verbose_name="Familiya")
    photo = models.ImageField(upload_to='students/', blank=True, null=True, verbose_name="Rasm")
    bio = models.TextField(verbose_name="O'quvchi haqida ma'lumot")
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_results', verbose_name="Kurs")
    video_file = models.FileField(upload_to='videos/students/', blank=True, null=True, help_text="O'quvchi videosi (faqat lokal fayl)", verbose_name="Video")
    video_url = models.URLField(blank=True, null=True, help_text="YouTube yoki Vimeo video havolasi", verbose_name="Video URL")
    achievement = models.CharField(max_length=200, blank=True, help_text="Muvaffaqiyat (masalan: IELTS 7.5, TOEFL 100)", verbose_name="Muvaffaqiyat")
    is_featured = models.BooleanField(default=False, verbose_name="Asosiy sahifada ko'rsatish")
    order = models.IntegerField(default=0, help_text="Tartib raqami (kichik raqamlar birinchi ko'rsatiladi)")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "O'quvchi natijasi"
        verbose_name_plural = "O'quvchilarning natijalari"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        """To'liq ism-familiya"""
        return f"{self.first_name} {self.last_name}"


class SATCourse(models.Model):
    """SAT uchun alohida kurslar modeli (admin orqali boshqariladi)."""
    LEVEL_CHOICES = Course.LEVEL_CHOICES

    title = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.CharField(max_length=100, help_text="e.g., '3 months', '6 weeks'")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    image = models.ImageField(upload_to='sat_courses/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Ko'rsatish tartibi (kichik raqam birinchi)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "SAT Course"
        verbose_name_plural = "SAT Courses"

    def __str__(self):
        return self.title


class TelegramConfig(models.Model):
    name = models.CharField(max_length=100, default="Asosiy sozlama")
    bot_token = models.CharField(max_length=255)
    chat_ids = models.TextField(
        help_text="Har bir chat ID ni yangi qatorda yozing (masalan: -100123..., -100456...)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Telegram sozlamasi"
        verbose_name_plural = "Telegram sozlamalari"

    def __str__(self):
        return self.name

    def get_chat_ids_list(self):
        return [chat_id.strip() for chat_id in self.chat_ids.splitlines() if chat_id.strip()]


class LandingSettings(models.Model):
    """Landing sahifa singleton sozlamalari (599k bazaviy offer)."""

    hero_headline = models.CharField(
        max_length=300,
        default='Kafolatlangan /\nIELTS - 7.0 + Online program',
    )
    hero_subtitle = models.TextField(
        default=(
            'IELTS balingizni Britaniyalik ustozlar va kafolatlangan tizim orqali o‘rganing'
        ),
    )
    hero_badge_text = models.CharField(
        max_length=200,
        default='UK ustoz + jonli darslar — joylar cheklangan',
        blank=True,
    )
    base_price = models.PositiveIntegerField(default=599_000)
    base_price_label = models.CharField(
        max_length=120,
        default='Platforma + jonli darslar — umrbod access',
    )
    pricing_card_title = models.CharField(max_length=120, default='Umrbod access')
    pricing_card_badge = models.CharField(max_length=80, default='ENG YAXSHI TAKLIF')
    reassurance_text = models.CharField(
        max_length=200,
        default='Bir martalik to‘lov • Jonli darslar • Umrbod access',
    )
    primary_cta_text = models.CharField(max_length=120, default='Bepul daraja testini boshlash')
    secondary_cta_text = models.CharField(max_length=120, default='Telegram orqali xarid qilish')
    telegram_purchase_url = models.URLField(default='https://t.me/tonacademyuz')
    platform_url = models.URLField(
        default='https://tonielts.uz/',
        help_text='«Sistemaga o‘tish» tugmasi — o‘quv platformasi (login).',
    )
    free_trial_url = models.CharField(max_length=300, default='/mock-tests/')
    stat_students = models.CharField(max_length=40, default='1000+')
    stat_students_label = models.CharField(max_length=80, default='talabalar')
    stat_improvement = models.CharField(max_length=40, default='95%')
    stat_improvement_label = models.CharField(
        max_length=120,
        default='o‘quvchilar kamida 1 bandga yaxshilandi',
    )
    instagram_url = models.URLField(blank=True, default='https://www.instagram.com/tonacademyuz/')
    youtube_url = models.URLField(blank=True, default='https://www.youtube.com/@TonAcademyuz')
    support_hours = models.CharField(
        max_length=120,
        blank=True,
        default='Dush–Shan: 09:00–20:00',
    )
    ga4_measurement_id = models.CharField(
        max_length=32,
        blank=True,
        help_text='Google Analytics 4 ID (masalan G-XXXXXXXX). Bo‘sh bo‘lsa o‘lchov yoqilmaydi.',
    )
    posthog_project_api_key = models.CharField(
        max_length=120,
        blank=True,
        help_text='PostHog Project token (phc_…). Bo‘sh bo‘lsa PostHog o‘chiq.',
    )
    posthog_api_host = models.URLField(
        blank=True,
        default='https://us.i.posthog.com',
        help_text='PostHog API host (US: https://us.i.posthog.com)',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Landing sozlamasi'
        verbose_name_plural = 'Landing sozlamalari'

    def __str__(self):
        return 'Landing sozlamalari'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def formatted_base_price(self):
        return f'{self.base_price:,}'.replace(',', ' ')


class PromoCampaign(models.Model):
    """Dynamic announcement bar, dolzarb taklif va yangiliklar."""

    PLACEMENT_CHOICES = [
        ('announcement', 'Announcement bar (tepa)'),
        ('current_offer', 'Dolzarb taklif (hero ostida)'),
        ('news', 'Yangilik / taklif kartasi'),
    ]
    BADGE_CHOICES = [
        ('new', 'Yangi'),
        ('live', 'LIVE'),
        ('limited', 'Limited'),
        ('webinar', 'Webinar'),
        ('intensive', 'Intensive'),
    ]

    enabled = models.BooleanField(default=False)
    placement = models.CharField(max_length=20, choices=PLACEMENT_CHOICES)
    badge = models.CharField(max_length=20, choices=BADGE_CHOICES, default='live')
    badge_custom = models.CharField(max_length=60, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    offer_label = models.CharField(
        max_length=120,
        blank=True,
        help_text='Masalan: LIVE bundle — 899 000 so‘m',
    )
    price = models.PositiveIntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    urgency_text = models.CharField(max_length=200, blank=True)
    cta_text = models.CharField(max_length=120, default='Telegram orqali qo‘shilish')
    cta_link = models.URLField(default='https://t.me/tonacademyuz')
    campaign_id = models.CharField(max_length=60, blank=True, help_text='Analytics uchun unique ID')
    image = models.ImageField(upload_to='landing/promo/', blank=True, null=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Promo kampaniya'
        verbose_name_plural = 'Promo kampaniyalar'

    def __str__(self):
        return f'{self.get_placement_display()}: {self.title}'

    @property
    def is_active_now(self):
        if not self.enabled:
            return False
        if self.expires_at:
            from django.utils import timezone
            if timezone.now() > self.expires_at:
                return False
        return True

    def display_badge(self):
        if self.badge_custom:
            return self.badge_custom
        return self.get_badge_display().upper()

    def formatted_price(self):
        if not self.price:
            return ''
        return f'{self.price:,}'.replace(',', ' ')


class PlatformPreview(models.Model):
    """Platforma preview tablari — real screenshotlar."""

    TAB_CHOICES = [
        ('all', 'Barchasi'),
        ('writing', 'Writing AI'),
        ('reading', 'Reading'),
        ('listening', 'Listening'),
        ('videos', 'Video darslar'),
        ('progress', 'Progress'),
    ]

    tab = models.CharField(max_length=20, choices=TAB_CHOICES, unique=True)
    title = models.CharField(max_length=120)
    image = models.ImageField(upload_to='landing/platform/', blank=True, null=True)
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Platforma preview'
        verbose_name_plural = 'Platforma previewlar'

    def __str__(self):
        return self.title


class LandingSectionCopy(models.Model):
    SECTION_CHOICES = [
        ('platform', 'Platforma'),
        ('benefits', 'Benefits'),
        ('ai', 'AI Checker'),
        ('results', 'Natijalar'),
        ('testimonials', 'Fikrlar'),
        ('news', 'Yangiliklar'),
        ('purchase', 'Xarid'),
        ('faq', 'FAQ'),
    ]

    section = models.CharField(max_length=30, choices=SECTION_CHOICES, unique=True)
    kicker = models.CharField(max_length=80)
    title = models.CharField(max_length=220)
    subtitle = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['section']
        verbose_name = 'Bo‘lim matni'
        verbose_name_plural = 'Bo‘lim matnlari'

    def __str__(self):
        return self.get_section_display()


class LandingHeroProof(models.Model):
    icon = models.CharField(max_length=100, help_text="Font Awesome icon class")
    title = models.CharField(max_length=120)
    subtitle = models.CharField(max_length=160)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Hero isbot'
        verbose_name_plural = 'Hero isbotlar'

    def __str__(self):
        return self.title


class LandingBenefitCard(models.Model):
    icon = models.CharField(max_length=100, help_text="Font Awesome icon class")
    title = models.CharField(max_length=160)
    text = models.TextField()
    badge = models.CharField(max_length=50, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Benefit kartasi'
        verbose_name_plural = 'Benefit kartalari'

    def __str__(self):
        return self.title


class LandingAICard(models.Model):
    KEY_CHOICES = [
        ('writing', 'Writing AI'),
        ('reading', 'Reading'),
        ('listening', 'Listening'),
    ]

    key = models.CharField(max_length=20, choices=KEY_CHOICES, unique=True)
    icon = models.CharField(max_length=100, help_text="Font Awesome icon class")
    title = models.CharField(max_length=160)
    text = models.TextField()
    video_file = models.FileField(
        upload_to='landing/ai/',
        blank=True,
        null=True,
        help_text='AI checker demo video (MP4/WebM). Rasm o‘rniga shu ko‘rsatiladi.',
    )
    video_url = models.URLField(
        blank=True,
        help_text='Ixtiyoriy YouTube/Vimeo havola. video_file bo‘lmasa shu ishlatiladi.',
    )
    poster_image = models.ImageField(
        upload_to='landing/ai/posters/',
        blank=True,
        null=True,
        help_text='Video poster (thumbnail). Bo‘sh bo‘lsa default preview chiqadi.',
    )
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'AI checker kartasi'
        verbose_name_plural = 'AI checker kartalari'

    def __str__(self):
        return self.title

    @property
    def has_video(self):
        return bool(self.video_file) or bool(self.video_url)
