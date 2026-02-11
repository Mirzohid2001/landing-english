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
    email = models.EmailField()
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
    email = models.EmailField()
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
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
    
    def __str__(self):
        return self.question


class ProcessStep(models.Model):
    ICON_CHOICES = [
        ('fas fa-user-plus', 'Sign Up'),
        ('fas fa-clipboard-check', 'Assessment'),
        ('fas fa-chalkboard-teacher', 'Learn'),
        ('fas fa-trophy', 'Excel'),
        ('fas fa-book', 'Book'),
        ('fas fa-certificate', 'Certificate'),
        ('fas fa-users', 'Users'),
        ('fas fa-graduation-cap', 'Graduation'),
    ]
    
    step_number = models.IntegerField(help_text="Step number (1, 2, 3, 4, etc.)")
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=100, choices=ICON_CHOICES, help_text="Font Awesome icon class")
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
